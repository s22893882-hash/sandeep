import { describe, it, expect, vi, beforeEach } from 'vitest';

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthService {
  login: (email: string, password: string) => Promise<{ token: string; user: User }>;
  logout: () => void;
  getToken: () => string | null;
  isAuthenticated: () => boolean;
}

const mockAuthService: AuthService = {
  login: vi.fn(async (email: string, password: string) => {
    if (email === 'test@example.com' && password === 'password') {
      return {
        token: 'mock-token',
        user: { id: 1, email, username: 'testuser' },
      };
    }
    throw new Error('Invalid credentials');
  }),
  logout: vi.fn(() => {
    localStorage.removeItem('token');
  }),
  getToken: vi.fn(() => {
    return localStorage.getItem('token');
  }),
  isAuthenticated: vi.fn(() => {
    return !!localStorage.getItem('token');
  }),
};

describe('Authentication Service', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should login with valid credentials', async () => {
    const result = await mockAuthService.login('test@example.com', 'password');
    
    expect(result).toBeDefined();
    expect(result.token).toBe('mock-token');
    expect(result.user.email).toBe('test@example.com');
  });

  it('should throw error with invalid credentials', async () => {
    await expect(
      mockAuthService.login('wrong@example.com', 'wrongpassword')
    ).rejects.toThrow('Invalid credentials');
  });

  it('should store token in localStorage', () => {
    localStorage.setItem('token', 'test-token');
    expect(mockAuthService.getToken()).toBe('test-token');
  });

  it('should clear token on logout', () => {
    localStorage.setItem('token', 'test-token');
    mockAuthService.logout();
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('should check authentication status', () => {
    expect(mockAuthService.isAuthenticated()).toBe(false);
    
    localStorage.setItem('token', 'test-token');
    expect(mockAuthService.isAuthenticated()).toBe(true);
  });
});
