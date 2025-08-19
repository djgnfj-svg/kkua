import { renderHook, act } from '@testing-library/react';
import guestStore from './guestStore';

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = mockLocalStorage;

describe('guestStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the store state before each test
    act(() => {
      guestStore.getState().resetGuestData();
    });
  });

  test('should initialize with default state', () => {
    const state = guestStore.getState();

    expect(state.nickname).toBe('');
    expect(state.lastLogin).toBeNull();
    expect(state.preferences).toEqual({
      notifications: true,
      sound: true,
    });
  });

  test('should set nickname correctly', () => {
    act(() => {
      guestStore.getState().setNickname('TestUser');
    });

    const state = guestStore.getState();
    expect(state.nickname).toBe('TestUser');
  });

  test('should update preferences correctly', () => {
    act(() => {
      guestStore.getState().setPreferences({ notifications: false });
    });

    const state = guestStore.getState();
    expect(state.preferences).toEqual({
      notifications: false,
      sound: true,
    });
  });

  test('should reset guest data correctly', () => {
    // First set some data
    act(() => {
      guestStore.getState().setNickname('TestUser');
      guestStore.getState().setPreferences({ sound: false });
    });

    // Then reset
    act(() => {
      guestStore.getState().resetGuestData();
    });

    const state = guestStore.getState();
    expect(state.nickname).toBe('');
    expect(state.lastLogin).toBeNull();
    expect(state.preferences).toEqual({
      notifications: true,
      sound: true,
    });
  });
});