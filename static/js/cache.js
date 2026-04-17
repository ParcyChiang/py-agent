// static/cache.js - 通用缓存工具

const CACHE_PREFIX = 'logistics_';

/**
 * 保存数据到localStorage
 * @param {string} key - 缓存键名
 * @param {any} value - 要缓存的数据
 */
function cacheSet(key, value) {
    try {
        const data = {
            value: value,
            timestamp: Date.now()
        };
        localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(data));
    } catch (e) {
        console.error('缓存保存失败:', e);
    }
}

/**
 * 从localStorage获取数据
 * @param {string} key - 缓存键名
 * @param {number} maxAge - 缓存最大有效期（毫秒），默认1小时
 * @returns {any} 缓存的数据，过期或不存在返回null
 */
function cacheGet(key, maxAge = 3600000) {
    try {
        const item = localStorage.getItem(CACHE_PREFIX + key);
        if (!item) return null;

        const data = JSON.parse(item);
        // 检查是否过期
        if (Date.now() - data.timestamp > maxAge) {
            localStorage.removeItem(CACHE_PREFIX + key);
            return null;
        }
        return data.value;
    } catch (e) {
        console.error('缓存读取失败:', e);
        return null;
    }
}

/**
 * 清除指定缓存
 * @param {string} key - 缓存键名
 */
function cacheRemove(key) {
    localStorage.removeItem(CACHE_PREFIX + key);
}

/**
 * 清除所有缓存
 */
function cacheClear() {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
        if (key.startsWith(CACHE_PREFIX)) {
            localStorage.removeItem(key);
        }
    });
}
