import { renderHook, act } from '@testing-library/react';
import useGuestStore from './guestStore';

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
    const { result } = renderHook(() => useGuestStore());
    act(() => {
      result.current.logout();
    });
  });

  test('should initialize with default state', () => {
    mockLocalStorage.getItem.mockReturnValue(null);
    const { result } = renderHook(() => useGuestStore());
    
    expect(result.current.guest).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('should login user correctly', () => {
    const { result } = renderHook(() => useGuestStore());
    const mockGuest = { guest_id: 1, nickname: 'TestUser' };
    
    act(() => {
      result.current.login(mockGuest);
    });
    
    expect(result.current.guest).toEqual(mockGuest);
    expect(result.current.isAuthenticated).toBe(true);
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('guest', JSON.stringify(mockGuest));
  });

  test('should logout user correctly', () => {
    const { result } = renderHook(() => useGuestStore());
    const mockGuest = { guest_id: 1, nickname: 'TestUser' };
    
    // First login
    act(() => {
      result.current.login(mockGuest);
    });
    
    // Then logout
    act(() => {
      result.current.logout();
    });
    
    expect(result.current.guest).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('guest');
  });

  test('should update nickname correctly', () => {
    const { result } = renderHook(() => useGuestStore());
    const mockGuest = { guest_id: 1, nickname: 'TestUser' };
    
    act(() => {
      result.current.login(mockGuest);
    });
    
    act(() => {
      result.current.updateNickname('NewNickname');
    });
    
    expect(result.current.guest.nickname).toBe('NewNickname');
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'guest', 
      JSON.stringify({ ...mockGuest, nickname: 'NewNickname' })
    );
  });
});