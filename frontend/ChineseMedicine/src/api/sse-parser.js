// SSE 行缓冲解析器：供 H5 fetch 与微信小程序分块请求共用。
export function createSseParser(handlers = {}) {
  let buffer = ''
  let finished = false

  const fail = (message) => {
    if (finished) return
    finished = true
    handlers.onError && handlers.onError(new Error(message))
  }
  const done = () => {
    if (finished) return
    finished = true
    handlers.onDone && handlers.onDone()
  }
  const consumeLine = (rawLine) => {
    const line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
    if (!line.startsWith('data:')) return
    // SSE 允许 data: 后保留一个可选空格；文本片段的其他空格必须原样保留。
    const data = line.slice(5).replace(/^ /, '')
    if (!data || finished) return
    if (data === '[DONE]') {
      done()
      return
    }
    if (data === '[METADATA]') {
      return
    }
    if (data.startsWith('{')) {
      try {
        handlers.onPayload && handlers.onPayload(JSON.parse(data))
      } catch (error) {
        fail('流式响应中的结构化结果格式错误')
      }
      return
    }
    handlers.onText && handlers.onText(data)
  }

  return {
    push(text) {
      if (finished || !text) return
      buffer += text
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      lines.forEach(consumeLine)
    },
    close() {
      if (finished) return
      if (buffer) consumeLine(buffer)
      if (!finished) fail('流式响应未正常结束')
    },
    error(error) {
      fail(error.message || '网络异常，请稍后重试')
    },
    isFinished() {
      return finished
    }
  }
}
