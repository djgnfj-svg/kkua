import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Loading from './Loading';

// Mock the guestStore
const mockLogin = jest.fn();
const mockGuest = null;
const mockIsAuthenticated = false;

jest.mock('../../store/guestStore', () => ({
  __esModule: true,
  default: () => ({
    guest: mockGuest,
    isAuthenticated: mockIsAuthenticated,
    login: mockLogin,
  }),
}));

// Mock axios
jest.mock('../../Api/axiosInstance', () => ({
  post: jest.fn(),
}));

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const renderLoading = () => {
  return render(
    <BrowserRouter>
      <Loading />
    </BrowserRouter>
  );
};

describe('Loading Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders welcome message and input form', () => {
    renderLoading();
    
    expect(screen.getByText(/끄아에 오신 걸 환영합니다/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/닉네임을 입력하세요/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /시작하기/i })).toBeInTheDocument();
  });

  test('updates nickname input when typed', () => {
    renderLoading();
    
    const nicknameInput = screen.getByPlaceholderText(/닉네임을 입력하세요/i);
    fireEvent.change(nicknameInput, { target: { value: 'TestUser' } });
    
    expect(nicknameInput.value).toBe('TestUser');
  });

  test('shows error for empty nickname', () => {
    renderLoading();
    
    const startButton = screen.getByRole('button', { name: /시작하기/i });
    fireEvent.click(startButton);
    
    expect(screen.getByText(/닉네임을 입력해주세요/i)).toBeInTheDocument();
  });

  test('shows error for nickname too short', () => {
    renderLoading();
    
    const nicknameInput = screen.getByPlaceholderText(/닉네임을 입력하세요/i);
    fireEvent.change(nicknameInput, { target: { value: 'A' } });
    
    const startButton = screen.getByRole('button', { name: /시작하기/i });
    fireEvent.click(startButton);
    
    expect(screen.getByText(/닉네임은 2~10자 사이여야 합니다/i)).toBeInTheDocument();
  });

  test('shows error for nickname too long', () => {
    renderLoading();
    
    const nicknameInput = screen.getByPlaceholderText(/닉네임을 입력하세요/i);
    fireEvent.change(nicknameInput, { target: { value: 'VeryLongNickname' } });
    
    const startButton = screen.getByRole('button', { name: /시작하기/i });
    fireEvent.click(startButton);
    
    expect(screen.getByText(/닉네임은 2~10자 사이여야 합니다/i)).toBeInTheDocument();
  });
});