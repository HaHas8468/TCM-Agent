// H5 生产部署使用同源 API，由边缘 Nginx 将 /api 反向代理到网关。
// 小程序等非 H5 端仍可在构建时通过 VITE_API_BASE_URL 指定完整服务地址。
let defaultBaseUrl = ''
// #ifndef H5
defaultBaseUrl = 'http://127.0.0.1'
// #endif
export const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? defaultBaseUrl

// 默认请求超时（毫秒）。后端 Agent 推理可能较慢，统一放宽到 120s。
// 注意：微信小程序平台自身上限为 60000ms，超出部分会被平台强制截断。
const DEFAULT_TIMEOUT = 120000

const TOKEN_KEY = 'cm-auth-token'
const PATIENT_ID_KEY = 'cm-patient-id'

let loadingCount = 0
let loadingShown = false

function showLoading(title = '加载中...') {
  loadingCount += 1
  if (loadingCount === 1 && !loadingShown) {
    loadingShown = true
    uni.showLoading({ title, mask: false })
  }
}

function hideLoading() {
  if (loadingCount <= 0) return
  loadingCount -= 1
  if (loadingCount === 0 && loadingShown) {
    loadingShown = false
    uni.hideLoading()
  }
}

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) {
    uni.setStorageSync(TOKEN_KEY, token)
  }
}

export function getPatientId() {
  return uni.getStorageSync(PATIENT_ID_KEY) || ''
}

export function setPatientId(id) {
  if (id) {
    uni.setStorageSync(PATIENT_ID_KEY, id)
  }
}

export function clearAuth() {
  uni.removeStorageSync(TOKEN_KEY)
  uni.removeStorageSync(PATIENT_ID_KEY)
}

// 判断是否为鉴权失效类错误（token 过期 / 未登录 / 未授权）
export function isAuthError(error) {
  if (!error) return false
  if (error.statusCode === 401) return true
  const message = error.message || ''
  return /token|登录|未授权|unauthor|expire|失效|请先登录|未认证/i.test(message)
}

function resolveErrorMessage(res) {
  const body = res.data
  if (body && typeof body === 'object' && body.msg) {
    return body.msg
  }
  if (res.statusCode === 0) return '网络异常，请稍后重试'
  return `请求失败（${res.statusCode}）`
}

/**
 * 统一请求封装
 * @param {Object} options
 * @param {String} options.url 接口路径（不含 baseURL）
 * @param {String} [options.method=GET]
 * @param {Object} [options.data]
 * @param {Object} [options.header]
 * @param {Boolean} [options.loading=false] 是否展示 loading
 * @param {Boolean} [options.auth=true] 是否携带 Bearer Token
 * @param {Boolean} [options.showError=true] 是否自动 toast 错误
 * @param {Boolean} [options.authRedirect=true] 鉴权失败时是否跳转登录页
 * @param {Number}  [options.timeout=DEFAULT_TIMEOUT] 超时时间（毫秒），默认 120s
 * @returns {Promise<any>} 成功时 resolve 响应体中的 data 字段
 */
export function request(options) {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    loading = false,
    auth = true,
    showError = true,
    authRedirect = true,
    timeout = DEFAULT_TIMEOUT
  } = options

  return new Promise((resolve, reject) => {
    const headers = Object.assign({ 'Content-Type': 'application/json' }, header)
    if (auth) {
      const token = getToken()
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }
    if (loading) {
      showLoading()
    }

    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: headers,
      timeout,
      success: (res) => {
        const body = res.data
        const ok =
          res.statusCode >= 200 &&
          res.statusCode < 300 &&
          body &&
          typeof body === 'object' &&
          body.code === 0

        if (ok) {
          if (loading) hideLoading()
          resolve(body.data)
          return
        }

        const message = resolveErrorMessage(res)
        const error = new Error(message)
        error.code = body && body.code
        error.statusCode = res.statusCode
        if (loading) hideLoading()
        if (showError) {
          uni.showToast({ title: message, icon: 'none' })
        }
        if (authRedirect && auth && isAuthError(error)) {
          clearAuth()
          uni.reLaunch({ url: '/pages/login/login' })
        }
        reject(error)
      },
      fail: (err) => {
        if (loading) hideLoading()
        const error = new Error('网络异常，请稍后重试')
        error.code = -1
        error.statusCode = 0
        error.raw = err
        if (showError) {
          uni.showToast({ title: error.message, icon: 'none' })
        }
        reject(error)
      }
    })
  })
}
