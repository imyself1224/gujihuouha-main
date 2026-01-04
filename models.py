"""
古籍事件关系识别 - 神经网络模型模块
包含所有模型架构定义
"""
import torch
import torch.nn as nn


class GraphConvolution(nn.Module):
    """图卷积层"""
    def __init__(self, in_features, out_features):
        super(GraphConvolution, self).__init__()
        self.linear = nn.Linear(in_features, out_features)
        self.relu = nn.ReLU()

    def forward(self, x, adj):
        support = self.linear(x)
        output = torch.bmm(adj, support)
        return self.relu(output)


class GuwenBERT_EventGraph(nn.Module):
    """基于事件图的古文BERT模型"""
    def __init__(self, bert_model, hidden_size=768, gcn_layers=2, num_relations=12):
        super(GuwenBERT_EventGraph, self).__init__()
        self.bert = bert_model
        self.gcn_layers = nn.ModuleList([GraphConvolution(hidden_size, hidden_size) for _ in range(gcn_layers)])
        self.dropout = nn.Dropout(0.2)
        self.classifier = nn.Linear(hidden_size * 2, num_relations)

    def forward(self, input_ids, attention_mask, e1_span, e2_span, adj):
        # 1. BERT编码
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # [batch, seq_len, hidden]

        # 2. 取出事件触发词span平均表示
        e1_repr = self.extract_span(sequence_output, e1_span)  # [batch, hidden]
        e2_repr = self.extract_span(sequence_output, e2_span)

        # 3. 事件图节点初始化
        event_nodes = torch.stack([e1_repr, e2_repr], dim=1)  # [batch, num_nodes, hidden]

        # 4. 图卷积传播
        for gcn in self.gcn_layers:
            event_nodes = gcn(event_nodes, adj)

        # 5. 拼接 head-tail 事件节点
        pair_repr = torch.cat([event_nodes[:, 0, :], event_nodes[:, 1, :]], dim=-1)
        pair_repr = self.dropout(pair_repr)

        # 6. 分类
        logits = self.classifier(pair_repr)
        return logits

    def extract_span(self, hidden, spans):
        # spans: (batch, 2)
        span_embeds = []
        for i, (start, end) in enumerate(spans):
            vec = hidden[i, start:end + 1, :].mean(dim=0)
            span_embeds.append(vec)
        return torch.stack(span_embeds, dim=0)


class GuwenBERT_EM(nn.Module):
    """实体匹配的古文BERT模型 - 拼接方法"""
    def __init__(self, bert_model, num_relations, hidden_size=768, dropout_rate=0.3):
        super(GuwenBERT_EM, self).__init__()
        self.bert = bert_model
        self.hidden_size = hidden_size
        self.dropout = nn.Dropout(dropout_rate)

        # 拼接向量：[e1, e2, |e1-e2|, e1*e2] → 4 * hidden_size
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 4, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size, num_relations)
        )

    def forward(self, input_ids, attention_mask, e1_span, e2_span):
        """
        input_ids: (B, L)
        attention_mask: (B, L)
        e1_span, e2_span: (B, 2) 分别是每个事件的起止位置 [start, end)
        """
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state  # (B, L, H)

        batch_size = input_ids.size(0)
        e1_vecs, e2_vecs = [], []

        for i in range(batch_size):
            e1_start, e1_end = e1_span[i]
            e2_start, e2_end = e2_span[i]
            # 平均池化实体表示
            e1_vec = torch.mean(last_hidden_state[i, e1_start:e1_end, :], dim=0)
            e2_vec = torch.mean(last_hidden_state[i, e2_start:e2_end, :], dim=0)
            e1_vecs.append(e1_vec)
            e2_vecs.append(e2_vec)

        e1_vecs = torch.stack(e1_vecs)  # (B, H)
        e2_vecs = torch.stack(e2_vecs)  # (B, H)

        # 拼接操作
        diff = torch.abs(e1_vecs - e2_vecs)
        mul = e1_vecs * e2_vecs
        concat = torch.cat([e1_vecs, e2_vecs, diff, mul], dim=1)  # (B, 4H)
        concat = self.dropout(concat)

        logits = self.classifier(concat)  # (B, num_relations)
        return logits


class GuwenBERT_BiLSTM_ATT(nn.Module):
    """双向LSTM+注意力机制"""
    def __init__(self, bert_model, num_relations, hidden_size=768, gru_hidden_size=256, gru_layers=1):
        super(GuwenBERT_BiLSTM_ATT, self).__init__()
        self.bert = bert_model
        
        self.bigru = nn.LSTM(
            input_size=hidden_size,
            hidden_size=gru_hidden_size,
            num_layers=gru_layers,
            bidirectional=True,
            batch_first=True
        )

        self.attention = nn.Sequential(
            nn.Linear(gru_hidden_size * 2, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(gru_hidden_size * 2, num_relations)

    def forward(self, input_ids, attention_mask, e1_start=None, e1_end=None, e2_start=None, e2_end=None):
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = bert_outputs.last_hidden_state  # (B, L, 768)

        gru_output, _ = self.bigru(sequence_output)  # (B, L, 2*gru_hidden_size)

        attn_scores = self.attention(gru_output)  # (B, L, 1)
        attn_weights = torch.softmax(attn_scores, dim=1)  # (B, L, 1)

        context = torch.sum(attn_weights * gru_output, dim=1)  # (B, 2*gru_hidden_size)

        out = self.dropout(context)
        logits = self.classifier(out)  # (B, num_relations)

        return logits


class GuwenBERT_BiGRU_ATT(nn.Module):
    """双向GRU+注意力机制"""
    def __init__(self, bert_model, num_relations, hidden_size=768, gru_hidden_size=256, gru_layers=1):
        super(GuwenBERT_BiGRU_ATT, self).__init__()
        self.bert = bert_model

        self.bigru = nn.GRU(
            input_size=hidden_size,
            hidden_size=gru_hidden_size,
            num_layers=gru_layers,
            bidirectional=True,
            batch_first=True
        )

        self.attention = nn.Sequential(
            nn.Linear(gru_hidden_size * 2, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(gru_hidden_size * 2, num_relations)

    def forward(self, input_ids, attention_mask, e1_start=None, e1_end=None, e2_start=None, e2_end=None):
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = bert_outputs.last_hidden_state  # (B, L, 768)

        gru_output, _ = self.bigru(sequence_output)  # (B, L, 2*gru_hidden_size)

        attn_scores = self.attention(gru_output)  # (B, L, 1)
        attn_weights = torch.softmax(attn_scores, dim=1)  # (B, L, 1)

        context = torch.sum(attn_weights * gru_output, dim=1)  # (B, 2*gru_hidden_size)

        out = self.dropout(context)
        logits = self.classifier(out)  # (B, num_relations)

        return logits


class GuwenBERT_CNN_ATT(nn.Module):
    """CNN+注意力机制"""
    def __init__(self, bert_model, num_relations, hidden_size=768, num_filters=256, kernel_sizes=(2, 3, 4)):
        super(GuwenBERT_CNN_ATT, self).__init__()
        self.bert = bert_model

        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=hidden_size,
                      out_channels=num_filters,
                      kernel_size=k)
            for k in kernel_sizes
        ])

        self.attention = nn.Sequential(
            nn.Linear(num_filters * len(kernel_sizes), 128),
            nn.Tanh(),
            nn.Linear(128, 1),
            nn.Softmax(dim=1)
        )

        self.dropout = nn.Dropout(0.3)
        self.classifier = nn.Linear(num_filters * len(kernel_sizes), num_relations)

    def forward(self, input_ids, attention_mask, e1_start=None, e1_end=None, e2_start=None, e2_end=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state  # (B, L, 768)

        x = sequence_output.transpose(1, 2)  # (B, 768, L)
        conv_outputs = [torch.relu(conv(x)) for conv in self.convs]

        pooled = [torch.max(co, dim=2)[0] for co in conv_outputs]
        cnn_output = torch.cat(pooled, dim=1)  # (B, num_filters * len(kernel_sizes))

        att_weights = self.attention(cnn_output)  # (B, 1)
        att_output = cnn_output * att_weights  # (B, feature_dim)

        out = self.dropout(att_output)
        logits = self.classifier(out)
        return logits


class GuwenBERT_BiLSTM(nn.Module):
    """双向LSTM模型"""
    def __init__(self, bert_model, num_relations, hidden_size=768, lstm_hidden_size=256, lstm_layers=2):
        super(GuwenBERT_BiLSTM, self).__init__()
        self.bert = bert_model
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_layers,
            bidirectional=True,
            batch_first=True
        )
        self.dropout = nn.Dropout(0.2)
        self.classifier = nn.Linear(lstm_hidden_size * 2, num_relations)

    def forward(self, input_ids, attention_mask, e1_start=None, e1_end=None, e2_start=None, e2_end=None):
        bert_outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = bert_outputs.last_hidden_state  # (B, L, 768)

        lstm_out, _ = self.lstm(last_hidden_state)  # (B, L, 2*lstm_hidden_size)

        pooled_output = torch.mean(lstm_out, dim=1)  # (B, 512)

        logits = self.classifier(self.dropout(pooled_output))  # (B, num_relations)
        return logits


class RBERT(nn.Module):
    """R-BERT模型 - 实体+上下文表示"""
    def __init__(self, bert_model, num_relations, hidden_size=768):
        super(RBERT, self).__init__()
        self.bert = bert_model
        self.num_relations = num_relations
        self.hidden_size = hidden_size

        self.classifier = nn.Linear(hidden_size * 3, num_relations)
        self.dropout = nn.Dropout(0.1)

    def forward(self, input_ids, attention_mask, e1_start, e1_end, e2_start, e2_end):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state

        batch_size = input_ids.size(0)

        e1_representations = []
        e2_representations = []
        context_representations = []

        for i in range(batch_size):
            # 实体1表示 (平均池化)
            e1_repr = torch.mean(last_hidden_state[i, e1_start[i]:e1_end[i], :], dim=0)
            e1_representations.append(e1_repr)

            # 实体2表示 (平均池化)
            e2_repr = torch.mean(last_hidden_state[i, e2_start[i]:e2_end[i], :], dim=0)
            e2_representations.append(e2_repr)

            # [CLS]标记作为上下文表示
            context_repr = last_hidden_state[i, 0, :]
            context_representations.append(context_repr)

        e1_rep = torch.stack(e1_representations)
        e2_rep = torch.stack(e2_representations)
        context_rep = torch.stack(context_representations)

        combined_rep = torch.cat([e1_rep, e2_rep, context_rep], dim=1)
        combined_rep = self.dropout(combined_rep)

        logits = self.classifier(combined_rep)
        return logits
