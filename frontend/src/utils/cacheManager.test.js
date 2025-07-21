import { cacheManager, invalidateCache } from './cacheManager';

describe('cacheManager', () => {
  beforeEach(() => {
    // Clear cache before each test
    Object.keys(cacheManager.cache).forEach(key => {
      delete cacheManager.cache[key];
    });
    jest.clearAllMocks();
  });

  test('stores and retrieves cached data', () => {
    const testData = { id: 1, name: 'test' };
    const key = 'test-key';

    cacheManager.set(key, testData);
    const retrieved = cacheManager.get(key);

    expect(retrieved).toEqual(testData);
  });

  test('returns null for non-existent key', () => {
    const result = cacheManager.get('non-existent-key');
    expect(result).toBeNull();
  });

  test('respects cache TTL', () => {
    jest.useFakeTimers();
    
    const testData = { id: 1, name: 'test' };
    const key = 'test-key';
    const ttl = 1000; // 1 second

    cacheManager.set(key, testData, ttl);
    
    // Should be available immediately
    expect(cacheManager.get(key)).toEqual(testData);

    // Fast-forward time beyond TTL
    jest.advanceTimersByTime(1001);

    // Should be expired now
    expect(cacheManager.get(key)).toBeNull();

    jest.useRealTimers();
  });

  test('uses default TTL when not specified', () => {
    jest.useFakeTimers();
    
    const testData = { id: 1, name: 'test' };
    const key = 'test-key';

    cacheManager.set(key, testData);
    
    // Should be available after 4 minutes (default TTL - 1 minute)
    jest.advanceTimersByTime(4 * 60 * 1000);
    expect(cacheManager.get(key)).toEqual(testData);

    // Should be expired after 6 minutes (beyond default TTL)
    jest.advanceTimersByTime(2 * 60 * 1000);
    expect(cacheManager.get(key)).toBeNull();

    jest.useRealTimers();
  });

  test('removes specific cache key', () => {
    const testData1 = { id: 1, name: 'test1' };
    const testData2 = { id: 2, name: 'test2' };
    const key1 = 'test-key-1';
    const key2 = 'test-key-2';

    cacheManager.set(key1, testData1);
    cacheManager.set(key2, testData2);

    cacheManager.remove(key1);

    expect(cacheManager.get(key1)).toBeNull();
    expect(cacheManager.get(key2)).toEqual(testData2);
  });

  test('clears all cache', () => {
    const testData1 = { id: 1, name: 'test1' };
    const testData2 = { id: 2, name: 'test2' };
    const key1 = 'test-key-1';
    const key2 = 'test-key-2';

    cacheManager.set(key1, testData1);
    cacheManager.set(key2, testData2);

    cacheManager.clear();

    expect(cacheManager.get(key1)).toBeNull();
    expect(cacheManager.get(key2)).toBeNull();
  });

  test('has method returns correct values', () => {
    const testData = { id: 1, name: 'test' };
    const key = 'test-key';

    expect(cacheManager.has(key)).toBe(false);

    cacheManager.set(key, testData);
    expect(cacheManager.has(key)).toBe(true);

    cacheManager.remove(key);
    expect(cacheManager.has(key)).toBe(false);
  });

  test('handles expired entries in has method', () => {
    jest.useFakeTimers();
    
    const testData = { id: 1, name: 'test' };
    const key = 'test-key';
    const ttl = 1000;

    cacheManager.set(key, testData, ttl);
    expect(cacheManager.has(key)).toBe(true);

    jest.advanceTimersByTime(1001);
    expect(cacheManager.has(key)).toBe(false);

    jest.useRealTimers();
  });

  test('overwrites existing cache entry', () => {
    const testData1 = { id: 1, name: 'test1' };
    const testData2 = { id: 2, name: 'test2' };
    const key = 'test-key';

    cacheManager.set(key, testData1);
    expect(cacheManager.get(key)).toEqual(testData1);

    cacheManager.set(key, testData2);
    expect(cacheManager.get(key)).toEqual(testData2);
  });

  test('handles null and undefined values', () => {
    const key1 = 'null-key';
    const key2 = 'undefined-key';

    cacheManager.set(key1, null);
    cacheManager.set(key2, undefined);

    expect(cacheManager.get(key1)).toBeNull();
    expect(cacheManager.get(key2)).toBeUndefined();
    expect(cacheManager.has(key1)).toBe(true);
    expect(cacheManager.has(key2)).toBe(true);
  });
});

describe('invalidateCache', () => {
  beforeEach(() => {
    // Clear cache before each test
    Object.keys(cacheManager.cache).forEach(key => {
      delete cacheManager.cache[key];
    });
    jest.clearAllMocks();
  });

  test('removes matching cache keys with pattern', () => {
    cacheManager.set('room-1-data', { id: 1 });
    cacheManager.set('room-2-data', { id: 2 });
    cacheManager.set('user-1-data', { id: 3 });

    invalidateCache('room');

    expect(cacheManager.get('room-1-data')).toBeNull();
    expect(cacheManager.get('room-2-data')).toBeNull();
    expect(cacheManager.get('user-1-data')).toEqual({ id: 3 });
  });

  test('removes exact match when pattern matches full key', () => {
    cacheManager.set('exact-key', { data: 'test' });
    cacheManager.set('another-key', { data: 'other' });

    invalidateCache('exact-key');

    expect(cacheManager.get('exact-key')).toBeNull();
    expect(cacheManager.get('another-key')).toEqual({ data: 'other' });
  });

  test('does nothing when no keys match pattern', () => {
    cacheManager.set('test-key-1', { data: 1 });
    cacheManager.set('test-key-2', { data: 2 });

    invalidateCache('nonexistent');

    expect(cacheManager.get('test-key-1')).toEqual({ data: 1 });
    expect(cacheManager.get('test-key-2')).toEqual({ data: 2 });
  });

  test('handles empty cache gracefully', () => {
    expect(() => {
      invalidateCache('any-pattern');
    }).not.toThrow();
  });

  test('is case sensitive', () => {
    cacheManager.set('Room-1-data', { id: 1 });
    cacheManager.set('room-2-data', { id: 2 });

    invalidateCache('room');

    expect(cacheManager.get('Room-1-data')).toEqual({ id: 1 });
    expect(cacheManager.get('room-2-data')).toBeNull();
  });

  test('works with special characters in patterns', () => {
    cacheManager.set('user-profile_1', { id: 1 });
    cacheManager.set('user-settings_1', { id: 2 });
    cacheManager.set('admin-profile', { id: 3 });

    invalidateCache('user-');

    expect(cacheManager.get('user-profile_1')).toBeNull();
    expect(cacheManager.get('user-settings_1')).toBeNull();
    expect(cacheManager.get('admin-profile')).toEqual({ id: 3 });
  });
});