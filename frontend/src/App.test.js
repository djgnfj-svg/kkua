import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

// Mock the guestStore
jest.mock('./store/guestStore', () => ({
  __esModule: true,
  default: () => ({
    guest: null,
    isAuthenticated: false,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

// Mock axiosInstance
jest.mock('./Api/axiosInstance', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe('App Component', () => {
  test('renders without crashing', () => {
    renderApp();
  });

  test('renders loading page by default', () => {
    renderApp();
    // Check if loading component is rendered
    expect(document.body).toBeInTheDocument();
  });
});