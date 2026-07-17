<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  entries: {
    type: Array,
    default: () => []
  },
  doctorName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['save-entry', 'delete-entry'])

const LIST_VIEW = 'list'
const FORM_VIEW = 'form'
const PAGE_SIZE = 2
const DATE_FILTER_OPTIONS = ['时间范围', '最近一个月', '最近半年', '一年以上']
const FIXED_CATEGORY_OPTIONS = ['全部栏目', '内科验案', '妇科验案', '经典医案研读']

const viewMode = ref(LIST_VIEW)
const editingId = ref('')
const keyword = ref('')
const categoryFilter = ref('全部栏目')
const dateFilter = ref('时间范围')
const currentPage = ref(1)
const formError = ref('')

const form = reactive(createEmptyForm(props.doctorName))

function getTodayString() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

function splitTags(value) {
  return String(value || '')
    .split(/[、，,；;\n]/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function joinTags(list) {
  return Array.isArray(list) ? list.filter(Boolean).join('、') : ''
}

function normalizeEntry(entry = {}) {
  const doctors = Array.isArray(entry.doctors)
    ? entry.doctors
        .map((item) => {
          if (typeof item === 'string') {
            return item.trim()
          }

          if (!item || typeof item !== 'object') {
            return null
          }

          const name = String(item.name || '').trim()
          const id = String(item.id || '').trim()

          if (!name) {
            return null
          }

          return id ? { name, id } : { name }
        })
        .filter(Boolean)
    : []
  return {
    id: String(entry.id || '').trim(),
    title: String(entry.title || '').trim(),
    author: String(entry.author || '').trim(),
    publishedAt: String(entry.publishedAt || '').trim(),
    category: String(entry.category || '').trim(),
    sourceUrl: String(entry.sourceUrl || '').trim(),
    summary: String(entry.summary || '').trim(),
    content: String(entry.content || '').trim(),
    diseases: Array.isArray(entry.diseases) ? entry.diseases.filter(Boolean) : [],
    syndromes: Array.isArray(entry.syndromes) ? entry.syndromes.filter(Boolean) : [],
    symptoms: Array.isArray(entry.symptoms) ? entry.symptoms.filter(Boolean) : [],
    formulas: Array.isArray(entry.formulas) ? entry.formulas.filter(Boolean) : [],
    treatment: String(entry.treatment || '').trim(),
    doctors
  }
}

function createEmptyForm(doctorName = '') {
  return {
    title: '',
    author: doctorName || '',
    publishedAt: getTodayString(),
    category: '',
    sourceUrl: '',
    summary: '',
    content: '',
    diseasesText: '',
    syndromesText: '',
    symptomsText: '',
    formulasText: '',
    treatment: ''
  }
}

function buildFormState(entry = {}) {
  const normalized = normalizeEntry(entry)

  return {
    title: normalized.title,
    author: props.doctorName || normalized.author || '',
    publishedAt: normalized.publishedAt || getTodayString(),
    category: normalized.category,
    sourceUrl: normalized.sourceUrl,
    summary: normalized.summary,
    content: normalized.content,
    diseasesText: joinTags(normalized.diseases),
    syndromesText: joinTags(normalized.syndromes),
    symptomsText: joinTags(normalized.symptoms),
    formulasText: joinTags(normalized.formulas),
    treatment: normalized.treatment
  }
}

function fillForm(nextState = {}) {
  Object.assign(form, createEmptyForm(props.doctorName), nextState)
}

function resetFilters() {
  keyword.value = ''
  categoryFilter.value = '全部栏目'
  dateFilter.value = '时间范围'
  currentPage.value = 1
}

function matchesDateFilter(dateText, rangeLabel) {
  if (rangeLabel === '时间范围') {
    return true
  }

  const publishedTime = new Date(dateText).getTime()

  if (!publishedTime) {
    return false
  }

  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const diffDays = Math.floor((todayStart - publishedTime) / (24 * 60 * 60 * 1000))

  if (rangeLabel === '最近一个月') {
    return diffDays >= 0 && diffDays <= 30
  }

  if (rangeLabel === '最近半年') {
    return diffDays >= 0 && diffDays <= 183
  }

  if (rangeLabel === '一年以上') {
    return diffDays > 365
  }

  return true
}

const normalizedEntries = computed(() => {
  return props.entries
    .map((entry) => normalizeEntry(entry))
    .sort((left, right) => {
      const rightTime = new Date(right.publishedAt || 0).getTime()
      const leftTime = new Date(left.publishedAt || 0).getTime()

      if (rightTime !== leftTime) {
        return rightTime - leftTime
      }

      return right.id.localeCompare(left.id)
    })
})

const editingEntry = computed(() => {
  return normalizedEntries.value.find((entry) => entry.id === editingId.value) || null
})

const categoryOptions = computed(() => {
  const values = normalizedEntries.value.map((entry) => entry.category).filter(Boolean)
  return Array.from(new Set(FIXED_CATEGORY_OPTIONS.concat(values)))
})

const filteredEntries = computed(() => {
  const searchValue = keyword.value.trim().toLowerCase()

  return normalizedEntries.value.filter((entry) => {
    const matchesKeyword =
      !searchValue ||
      [
        entry.title,
        entry.author,
        entry.summary,
        entry.content,
        entry.category,
        entry.treatment,
        entry.diseases.join(' '),
        entry.syndromes.join(' '),
        entry.symptoms.join(' '),
        entry.formulas.join(' ')
      ]
        .join(' ')
        .toLowerCase()
        .includes(searchValue)

    const matchesCategory = categoryFilter.value === '全部栏目' || entry.category === categoryFilter.value
    const matchesDate = matchesDateFilter(entry.publishedAt, dateFilter.value)

    return matchesKeyword && matchesCategory && matchesDate
  })
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredEntries.value.length / PAGE_SIZE))
})

const pagedEntries = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredEntries.value.slice(start, start + PAGE_SIZE)
})

const pageItems = computed(() => {
  const total = totalPages.value

  if (total <= 7) {
    return Array.from({ length: total }, (_, index) => index + 1)
  }

  const items = [1]
  const start = Math.max(2, currentPage.value - 1)
  const end = Math.min(total - 1, currentPage.value + 1)

  if (start > 2) {
    items.push('left-ellipsis')
  }

  for (let page = start; page <= end; page += 1) {
    items.push(page)
  }

  if (end < total - 1) {
    items.push('right-ellipsis')
  }

  items.push(total)
  return items
})

const hasActiveFilters = computed(() => {
  return keyword.value.trim() || categoryFilter.value !== '全部栏目' || dateFilter.value !== '时间范围'
})

watch(
  () => [keyword.value, categoryFilter.value, dateFilter.value],
  () => {
    currentPage.value = 1
  }
)

watch(
  () => totalPages.value,
  (value) => {
    if (currentPage.value > value) {
      currentPage.value = value
    }
  }
)

watch(
  () => props.doctorName,
  (value) => {
    form.author = value || ''
  }
)

function openCreateView() {
  editingId.value = ''
  formError.value = ''
  fillForm()
  viewMode.value = FORM_VIEW
}

function openEditView(entry) {
  editingId.value = entry.id
  formError.value = ''
  fillForm(buildFormState(entry))
  viewMode.value = FORM_VIEW
}

function returnToList() {
  viewMode.value = LIST_VIEW
  formError.value = ''
}

function clearForm() {
  if (editingEntry.value) {
    fillForm(buildFormState(editingEntry.value))
    return
  }

  fillForm()
}

function buildSubmitPayload() {
  return {
    ...(editingId.value ? { id: editingId.value } : {}),
    title: form.title,
    author: props.doctorName || form.author,
    publishedAt: form.publishedAt,
    category: form.category,
    sourceUrl: form.sourceUrl,
    summary: form.summary,
    content: form.content,
    diseases: splitTags(form.diseasesText),
    syndromes: splitTags(form.syndromesText),
    symptoms: splitTags(form.symptomsText),
    formulas: splitTags(form.formulasText),
    treatment: form.treatment
  }
}

async function submitEntry() {
  if (!form.title.trim()) {
    formError.value = '请先填写医案标题。'
    return
  }

  formError.value = ''

  try {
    await new Promise((resolve, reject) => {
      emit('save-entry', buildSubmitPayload(), { resolve, reject })
    })
    currentPage.value = 1
    returnToList()
  } catch (error) {
    formError.value = error instanceof Error ? error.message : '医案提交失败，请稍后重试。'
  }
}

async function deleteEntry(entry) {
  if (!entry?.id) {
    return
  }

  if (window.confirm(`确认删除医案“${entry.title}”吗？`)) {
    try {
      await new Promise((resolve, reject) => {
        emit('delete-entry', entry.id, { resolve, reject })
      })
    } catch (error) {
      formError.value = error instanceof Error ? error.message : '医案删除失败，请稍后重试。'
    }
  }
}
</script>

<template>
  <div class="case-library">
    <template v-if="viewMode === LIST_VIEW">
      <div class="header-bar header-bar--list">
        <button type="button" class="btn-primary" @click="openCreateView">+ 新增医案</button>
      </div>

      <div class="filter-console">
        <div class="filter-console__inner">
          <input
            v-model="keyword"
            class="search-input"
            type="text"
            placeholder="搜索医案标题、录入人、症状或方剂 (支持自然语言)"
          />

          <select v-model="categoryFilter" class="filter-select">
            <option v-for="option in categoryOptions" :key="option" :value="option">
              {{ option }}
            </option>
          </select>

          <select v-model="dateFilter" class="filter-select">
            <option v-for="option in DATE_FILTER_OPTIONS" :key="option" :value="option">
              {{ option }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="pagedEntries.length" class="case-list">
        <article v-for="entry in pagedEntries" :key="entry.id" class="case-card">
          <div class="card-header">
            <div>
              <button type="button" class="case-title" @click="openEditView(entry)">{{ entry.title }}</button>
              <div class="case-meta">
                <span>{{ entry.category || '未分类' }}</span>
                <span>医生/录入人：{{ entry.author || doctorName || '未填写' }}</span>
                <span>{{ entry.publishedAt || '未填写日期' }}</span>
              </div>
            </div>

            <div class="card-actions">
              <button type="button" class="btn-text" @click="openEditView(entry)">编辑</button>
              <button type="button" class="btn-text btn-text--danger" @click="deleteEntry(entry)">删除</button>
            </div>
          </div>

          <div class="case-summary">摘要：{{ entry.summary || '暂无摘要' }}</div>

          <div class="entity-tags">
            <span v-for="item in entry.diseases" :key="`disease-${entry.id}-${item}`" class="tag tag-disease">病名: {{ item }}</span>
            <span v-for="item in entry.syndromes" :key="`syndrome-${entry.id}-${item}`" class="tag tag-syndrome">
              证型: {{ item }}
            </span>
            <span v-for="item in entry.formulas" :key="`formula-${entry.id}-${item}`" class="tag tag-formula">方剂: {{ item }}</span>
          </div>
        </article>
      </div>

      <div v-else class="empty-state case-library__empty">
        <strong>{{ hasActiveFilters ? '当前筛选条件下暂无医案' : '当前还没有医案数据' }}</strong>
        <span>{{ hasActiveFilters ? '可调整搜索词、栏目或时间范围后重试。' : '可点击右上角“新增医案”开始录入。' }}</span>
        <div class="case-library__empty-actions">
          <button v-if="hasActiveFilters" type="button" class="ghost-button" @click="resetFilters">清空筛选</button>
          <button type="button" class="primary-button" @click="openCreateView">新增医案</button>
        </div>
      </div>

      <div v-if="filteredEntries.length > PAGE_SIZE" class="pagination">
        <button
          type="button"
          class="page-btn"
          :disabled="currentPage === 1"
          @click="currentPage = Math.max(1, currentPage - 1)"
        >
          &lt;
        </button>

        <button
          v-for="item in pageItems"
          :key="item"
          type="button"
          class="page-btn"
          :class="{ active: item === currentPage, 'page-btn--ellipsis': typeof item !== 'number' }"
          :disabled="typeof item !== 'number'"
          @click="typeof item === 'number' ? (currentPage = item) : null"
        >
          {{ typeof item === 'number' ? item : '…' }}
        </button>

        <button
          type="button"
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
        >
          &gt;
        </button>
      </div>
    </template>

    <template v-else>
      <div class="header-box">
        <div>
          <h1 class="page-title">医案录入</h1>
          <p class="page-tips">单条医案写入 Neo4j 知识图谱 · 标签字段可用逗号/顿号分隔多个值</p>
        </div>

        <button type="button" class="btn-text btn-back" @click="returnToList">返回医案库</button>
      </div>

      <div class="case-card case-card--form">
        <form class="case-form" @submit.prevent="submitEntry">
          <div class="section-group">
            <div class="section-header">基础信息</div>
            <div class="form-grid">
              <div class="form-group full-width">
                <label class="form-label">医案标题<span>*</span></label>
                <input v-model="form.title" type="text" class="form-control" placeholder="如：张氏治眩晕验案" />
              </div>
              <div class="form-group">
                <label class="form-label">医生/录入人<em>当前登录医生</em></label>
                <input
                  v-model="form.author"
                  type="text"
                  class="form-control"
                  placeholder="自动带入当前登录医生"
                  readonly
                />
              </div>
              <div class="form-group">
                <label class="form-label">发布日期</label>
                <input v-model="form.publishedAt" type="date" class="form-control" />
              </div>
              <div class="form-group">
                <label class="form-label">栏目<em>分类标签</em></label>
                <input v-model="form.category" type="text" class="form-control" placeholder="如：内科验案" />
              </div>
              <div class="form-group">
                <label class="form-label">来源链接</label>
                <input v-model="form.sourceUrl" type="text" class="form-control" placeholder="https://..." />
              </div>
            </div>
          </div>

          <div class="section-group">
            <div class="section-header">内容详述</div>
            <div class="form-group full-width section-group__spaced">
              <label class="form-label">摘要<em>辨证思路 / 疗效概述</em></label>
              <textarea v-model="form.summary" class="form-control" placeholder="简要概括本案辨证与治法..."></textarea>
            </div>
            <div class="form-group full-width">
              <label class="form-label">原文<em>医案全文内容</em></label>
              <textarea
                v-model="form.content"
                class="form-control original-area"
                placeholder="患者某某，男，岁......"
              ></textarea>
            </div>
          </div>

          <div class="section-group">
            <div class="section-header">诊疗信息</div>
            <div class="entity-box">
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label">病名</label>
                  <input v-model="form.diseasesText" type="text" class="form-control entity-control" placeholder="如：高血压, 眩晕" />
                </div>
                <div class="form-group">
                  <label class="form-label">证型</label>
                  <input
                    v-model="form.syndromesText"
                    type="text"
                    class="form-control entity-control"
                    placeholder="如：肝阳上亢, 痰湿中阻"
                  />
                </div>
                <div class="form-group">
                  <label class="form-label">症状</label>
                  <input v-model="form.symptomsText" type="text" class="form-control entity-control" placeholder="如：头痛, 失眠" />
                </div>
                <div class="form-group">
                  <label class="form-label">方剂</label>
                  <input v-model="form.formulasText" type="text" class="form-control entity-control" placeholder="如：天麻钩藤饮" />
                </div>
                <div class="form-group">
                  <label class="form-label">治法</label>
                  <input v-model="form.treatment" type="text" class="form-control entity-control" placeholder="如：平肝潜阳" />
                </div>
              </div>
            </div>
          </div>

          <p v-if="formError" class="case-form__error">{{ formError }}</p>

          <div class="form-actions">
            <button type="submit" class="btn btn-submit">{{ editingId ? '保存医案' : '提交医案' }}</button>
            <button type="button" class="btn btn-clear" @click="clearForm">清空</button>
          </div>
        </form>
      </div>
    </template>
  </div>
</template>

<style scoped>
.case-library {
  display: grid;
  gap: 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: var(--brand-deep);
  font-weight: 600;
}

.page-tips {
  margin: 4px 0 0;
  color: var(--text-subtle);
  font-size: 13px;
}

.header-bar,
.header-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.header-bar--list {
  justify-content: flex-end;
  margin-top: -2px;
}

.header-box {
  align-items: flex-end;
}

.btn-primary {
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  background: var(--brand);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  box-shadow: 0 4px 12px rgba(45, 106, 79, 0.2);
  transition: all 0.2s;
}

.btn-primary:hover {
  background: var(--brand-deep);
  transform: translateY(-1px);
}

.btn-text {
  border: none;
  background: none;
  padding: 0;
  color: var(--text-subtle);
  font-size: 13px;
  font-weight: 500;
  transition: color 0.2s;
}

.btn-text:hover {
  color: var(--brand);
}

.btn-text--danger {
  color: #d32f2f;
}

.btn-back {
  font-size: 14px;
}

.filter-console {
  border: 1px solid #e0eae4;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(45, 106, 79, 0.04);
  padding: 20px 24px;
}

.filter-console__inner {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input,
.filter-select {
  min-height: 46px;
  border: 1px solid #e0eae4;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  background: #fafcfb;
}

.search-input:focus {
  border-color: var(--brand);
  background: #fff;
}

.filter-select {
  min-width: 154px;
  padding: 12px 36px 12px 16px;
  color: var(--text-main);
  background-color: #fff;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23677A71' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 14px;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.case-card {
  border: 1px solid #e0eae4;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 4px 12px rgba(45, 106, 79, 0.04);
  padding: 24px;
  transition: all 0.2s ease;
}

.case-card:hover {
  border-color: #b9d0c3;
  box-shadow: 0 8px 24px rgba(45, 106, 79, 0.08);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.case-title {
  border: none;
  padding: 0;
  background: none;
  margin: 0;
  color: var(--brand-deep);
  font-size: 18px;
  font-weight: 600;
  text-align: left;
  transition: color 0.2s;
}

.case-title:hover {
  color: var(--brand);
}

.case-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
  color: var(--text-subtle);
  font-size: 13px;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.case-summary {
  margin-top: 12px;
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.6;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  padding-top: 16px;
  border-top: 1px dashed #e9f0ed;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.tag-disease {
  background: #fff3e0;
  color: #e65100;
}

.tag-syndrome {
  background: #e8f5e9;
  color: var(--brand-deep);
}

.tag-formula {
  background: #e3f2fd;
  color: #1565c0;
}

.case-library__empty {
  display: grid;
  gap: 14px;
}

.case-library__empty-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 32px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #e0eae4;
  border-radius: 8px;
  background: #fff;
  color: var(--text-subtle);
  font-size: 13px;
  transition: 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--brand);
  color: var(--brand);
}

.page-btn.active {
  background: var(--brand);
  color: #fff;
  border-color: var(--brand);
}

.page-btn--ellipsis {
  cursor: default;
}

.page-btn:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.case-card--form {
  max-width: 1000px;
  padding: 32px;
}

.section-group {
  margin-bottom: 32px;
}

.section-group__spaced {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  margin-bottom: 20px;
  padding-left: 4px;
  border-left: 4px solid var(--brand);
  color: var(--brand);
  font-size: 16px;
  font-weight: 600;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.full-width {
  grid-column: span 2;
}

.form-label {
  font-size: 13px;
  color: var(--text-main);
  font-weight: 600;
}

.form-label span {
  color: #d32f2f;
  margin-left: 4px;
}

.form-label em {
  font-style: normal;
  font-weight: 400;
  color: var(--text-subtle);
  margin-left: 8px;
}

.form-control {
  padding: 12px 14px;
  border: 1px solid #e0eae4;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
  background-color: #fafcfb;
}

.form-control:focus {
  border-color: var(--brand);
  background-color: #fff;
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.08);
}

.form-control[readonly] {
  background-color: #f3f6f4;
  color: var(--text-subtle);
  cursor: default;
}

textarea.form-control {
  resize: vertical;
  min-height: 80px;
  line-height: 1.6;
}

.original-area {
  min-height: 160px;
}

.entity-box {
  background-color: #f8fafb;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e9f0ed;
}

.entity-control {
  background-color: #fff;
  border-color: #d1dcd6;
}

.case-form__error {
  margin: 0 0 16px;
  color: #d32f2f;
  font-size: 15px;
  font-weight: 600;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #f0f5f2;
}

.btn {
  padding: 12px 28px;
  border-radius: 8px;
  border: none;
  font-size: 15px;
  font-weight: 700;
}

.btn-submit {
  flex: 0 0 220px;
  width: 220px;
  background-color: var(--brand);
  color: #fff;
  box-shadow: 0 4px 12px rgba(45, 106, 79, 0.2);
}

.btn-submit:hover {
  background-color: var(--brand-deep);
  transform: translateY(-1px);
}

.btn-clear {
  flex: 0 0 96px;
  width: 96px;
  background-color: #fff;
  color: var(--text-subtle);
  border: 1px solid #e0eae4;
  white-space: nowrap;
}

.btn-clear:hover {
  background-color: #f9fafb;
  color: var(--text-main);
}

@media (max-width: 1280px) {
  .filter-console__inner,
  .header-box,
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-bar {
    justify-content: flex-end;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .full-width {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .case-card,
  .case-card--form,
  .filter-console {
    padding: 20px;
  }

  .form-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-submit,
  .btn-clear {
    width: 100%;
    flex-basis: auto;
  }
}
</style>
