const USER_PROFILE_STORAGE_KEY = 'cm-current-user-profile'

export const avatarOptions = ['/static/head/head1.png', '/static/head/head2.png']

const LEGACY_DEFAULT_NAME = '孙**'

export const defaultUserProfile = Object.freeze({
	name: '张雪峰',
	avatar: '/static/head/head1.png',
	gender: '女',
	birth: '1997-08-16',
	age: '28',
	phone: '13800138000',
	allergyHistory: '无'
})

function parseStoredProfile(value) {
	if (!value) {
		return null
	}

	if (typeof value === 'string') {
		try {
			return JSON.parse(value)
		} catch (error) {
			return null
		}
	}

	if (typeof value === 'object') {
		return value
	}

	return null
}

function normalizeAvatar(avatar) {
	if (avatarOptions.includes(avatar)) {
		return avatar
	}

	return defaultUserProfile.avatar
}

function normalizeName(name) {
	if (typeof name !== 'string') {
		return defaultUserProfile.name
	}

	const trimmedName = name.trim()
	if (trimmedName === LEGACY_DEFAULT_NAME) {
		return defaultUserProfile.name
	}

	return trimmedName || defaultUserProfile.name
}

function normalizeUserProfile(profile = {}) {
	const { city, ...profileWithoutCity } = profile

	return {
		...defaultUserProfile,
		...profileWithoutCity,
		name: normalizeName(profileWithoutCity.name),
		avatar: normalizeAvatar(profileWithoutCity.avatar),
		age: `${profileWithoutCity.age || defaultUserProfile.age}`.trim(),
		allergyHistory: `${profileWithoutCity.allergyHistory || defaultUserProfile.allergyHistory}`.trim()
	}
}

export function getCurrentUserProfile() {
	const storedProfile = parseStoredProfile(uni.getStorageSync(USER_PROFILE_STORAGE_KEY))

	if (!storedProfile) {
		return {
			...defaultUserProfile
		}
	}

	return normalizeUserProfile(storedProfile)
}

export function saveCurrentUserProfile(profile) {
	const normalizedProfile = normalizeUserProfile(profile)
	uni.setStorageSync(USER_PROFILE_STORAGE_KEY, normalizedProfile)
	return normalizedProfile
}

export function resetCurrentUserProfile() {
	uni.removeStorageSync(USER_PROFILE_STORAGE_KEY)
	return {
		...defaultUserProfile
	}
}
