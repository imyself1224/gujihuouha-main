"""
古籍事件关系识别 - 推理模块
包含单个样本预测功能
"""
import torch


def predict_single(model, tokenizer, text, head_trigger, tail_trigger, id_to_relation, device):
    """
    对单个样本进行预测
    
    Args:
        model: 训练好的模型
        tokenizer: 分词器
        text: str, 原始文本
        head_trigger: str, 头事件触发词
        tail_trigger: str, 尾事件触发词
        id_to_relation: dict, ID到关系类型的映射
        device: torch.device, 设备
    
    Returns:
        tuple: (预测的关系类型, 概率分布数组)
    """
    model.eval()

    # 参数验证
    if not text or not head_trigger or not tail_trigger:
        print("Error: text, head_trigger, and tail_trigger must not be empty")
        return None, None

    # 添加实体标记 - 先标记头事件，再标记尾事件
    try:
        # 找到头事件触发词位置
        head_idx = text.find(head_trigger)
        if head_idx == -1:
            print(f"Error: head_trigger '{head_trigger}' not found in text")
            return None, None
        
        # 找到尾事件触发词位置
        tail_idx = text.find(tail_trigger, head_idx + len(head_trigger))
        if tail_idx == -1:
            print(f"Error: tail_trigger '{tail_trigger}' not found in text after head_trigger")
            return None, None
        
        # 构建带有实体标记的文本
        text_with_entities = (
            text[:head_idx] +
            "<e1>" + head_trigger + "</e1>" +
            text[head_idx + len(head_trigger):tail_idx] +
            "<e2>" + tail_trigger + "</e2>" +
            text[tail_idx + len(tail_trigger):]
        )
        
        print(f"Marked text: {text_with_entities}")
        
    except Exception as e:
        print(f"Error in entity marking: {str(e)}")
        return None, None

    # 分词
    try:
        inputs = tokenizer(
            text_with_entities,
            padding='max_length',
            truncation=True,
            max_length=256,
            return_tensors='pt'
        )
    except Exception as e:
        print(f"Error in tokenization: {str(e)}")
        return None, None

    # 获取实体位置
    input_ids = inputs['input_ids'][0].tolist()
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    
    print(f"Tokens: {tokens}")

    try:
        # 查找特殊token位置 - 基于tokenized的位置
        try:
            e1_pos = next(i for i, t in enumerate(tokens) if t == '<e1>')
            e1_end_pos = next(i for i, t in enumerate(tokens) if t == '</e1>')
            e2_pos = next(i for i, t in enumerate(tokens) if t == '<e2>')
            e2_end_pos = next(i for i, t in enumerate(tokens) if t == '</e2>')
        except StopIteration:
            print("Error: Could not find entity markers in tokens")
            print(f"Available tokens: {tokens}")
            return None, None
        
        # 实体span位置 (不包括标记符号本身)
        e1_start = e1_pos + 1
        e1_end = e1_end_pos
        e2_start = e2_pos + 1
        e2_end = e2_end_pos
        
        print(f"Entity positions - e1: ({e1_start}, {e1_end}), e2: ({e2_start}, {e2_end})")

        with torch.no_grad():
            # 为 GuwenBERT_EM 模型准备 span 张量 (batch_size, 2)
            e1_span = torch.tensor([[e1_start, e1_end]], dtype=torch.long).to(device)
            e2_span = torch.tensor([[e2_start, e2_end]], dtype=torch.long).to(device)
            
            outputs = model(
                inputs['input_ids'].to(device),
                inputs['attention_mask'].to(device),
                e1_span,
                e2_span
            )

            probs = torch.softmax(outputs, dim=1)
            predicted_class = torch.argmax(probs, dim=1).item()

            return id_to_relation[predicted_class], probs[0].cpu().numpy()

    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None


def predict_batch(model, tokenizer, samples, id_to_relation, device):
    """
    对一批样本进行预测
    
    Args:
        model: 训练好的模型
        tokenizer: 分词器
        samples: list, 样本列表，每个样本包含 original_text, head_trigger, tail_trigger
        id_to_relation: dict, ID到关系类型的映射
        device: torch.device, 设备
    
    Returns:
        list, 预测结果列表
    """
    predictions = []
    for sample in samples:
        text = sample['original_text']
        head_trigger = sample['head_trigger']
        tail_trigger = sample['tail_trigger']
        
        predicted_relation, probabilities = predict_single(
            model, tokenizer, text, head_trigger, tail_trigger, id_to_relation, device
        )
        
        predictions.append({
            'text': text,
            'head_trigger': head_trigger,
            'tail_trigger': tail_trigger,
            'predicted_relation': predicted_relation,
            'probabilities': probabilities
        })
    
    return predictions
