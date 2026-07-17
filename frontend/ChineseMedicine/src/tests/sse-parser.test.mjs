import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

// 项目源码为 Vite 的 ES module .js；测试运行器不改变 package 的模块类型，
// 因此将同一份源码作为 data URL 导入，避免仅为测试改动应用运行时配置。
const parserSource = readFileSync(new URL('../api/sse-parser.js', import.meta.url), 'utf8')
const { createSseParser } = await import(
  `data:text/javascript;base64,${Buffer.from(parserSource).toString('base64')}`
)

function makeParser() {
  const result = { text: [], payload: [], done: 0, error: [] }
  const parser = createSseParser({
    onText: (text) => result.text.push(text),
    onPayload: (payload) => result.payload.push(payload),
    onDone: () => { result.done += 1 },
    onError: (error) => result.error.push(error.message)
  })
  return { parser, result }
}

test('parses split text, structured payload, and a single completion', () => {
  const { parser, result } = makeParser()
  parser.push('data: 您好，')
  parser.push('请补充症状\n\ndata: {"status":"asking","ask_round":1}\n\ndata: [DONE]\n')
  parser.push('data: ignored\n')

  assert.deepEqual(result.text, ['您好，请补充症状'])
  assert.deepEqual(result.payload, [{ status: 'asking', ask_round: 1 }])
  assert.equal(result.done, 1)
  assert.deepEqual(result.error, [])
})

test('preserves text spaces and accepts CRLF frames', () => {
  const { parser, result } = makeParser()
  parser.push('data: 保留  两个空格\r\ndata: [DONE]\r\n')

  assert.deepEqual(result.text, ['保留  两个空格'])
  assert.equal(result.done, 1)
})

test('accepts UTF-8 text split across transport chunks', () => {
  const { parser, result } = makeParser()
  const bytes = new TextEncoder().encode('data: 症状加重\n')
  const decoder = new TextDecoder('utf-8')
  parser.push(decoder.decode(bytes.slice(0, 8), { stream: true }))
  parser.push(decoder.decode(bytes.slice(8), { stream: true }))
  parser.push(decoder.decode())

  assert.deepEqual(result.text, ['症状加重'])
})

test('reports invalid structured payload and incomplete streams once', () => {
  const malformed = makeParser()
  malformed.parser.push('data: {bad json}\n')
  malformed.parser.close()
  assert.deepEqual(malformed.result.error, ['流式响应中的结构化结果格式错误'])

  const incomplete = makeParser()
  incomplete.parser.push('data: 仍在输出')
  incomplete.parser.close()
  assert.deepEqual(incomplete.result.text, ['仍在输出'])
  assert.deepEqual(incomplete.result.error, ['流式响应未正常结束'])
})
