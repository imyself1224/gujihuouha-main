import { createApp } from 'vue'
import App from './App.vue'

// --- 必须添加下面这两行 ---
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// ------------------------

// ResizeObserver loop error fix
const debounce = (fn, delay) => {
  let timer = null;
  return function () {
    let context = this;
    let args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () {
      fn.apply(context, args);
    }, delay);
  }
}

const _ResizeObserver = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends _ResizeObserver {
  constructor(callback) {
    callback = debounce(callback, 16);
    super(callback);
  }
}

const app = createApp(App)

// --- 必须添加这一行 ---
app.use(ElementPlus)
// -------------------

// 全局错误处理
app.config.errorHandler = (err, instance, info) => {
  // 忽略 ResizeObserver 循环错误 (Element Plus/常见库已知问题)
  if (err && err.message && err.message.includes('ResizeObserver loop')) {
    return false
  }
  // 打印详细错误信息到控制台以便调试
  console.error('应用错误:', {
    message: err?.message,
    stack: err?.stack,
    info: info
  })
}

app.mount('#app')

