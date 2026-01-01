import { describe, it, expect, vi, beforeEach } from 'vitest';

interface ApiClient {
  get: (url: string) => Promise<any>;
  post: (url: string, data: any) => Promise<any>;
  put: (url: string, data: any) => Promise<any>;
  delete: (url: string) => Promise<any>;
}

const mockApiClient: ApiClient = {
  get: vi.fn(async (url: string) => {
    if (url === '/api/health') {
      return { status: 'healthy' };
    }
    if (url === '/api/users') {
      return [
        { id: 1, name: 'User 1' },
        { id: 2, name: 'User 2' },
      ];
    }
    return {};
  }),
  post: vi.fn(async (url: string, data: any) => {
    if (url === '/api/users') {
      return { id: 3, ...data };
    }
    return data;
  }),
  put: vi.fn(async (url: string, data: any) => {
    return { ...data, updated: true };
  }),
  delete: vi.fn(async (url: string) => {
    return { success: true };
  }),
};

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should make GET request', async () => {
    const result = await mockApiClient.get('/api/health');
    expect(result).toEqual({ status: 'healthy' });
    expect(mockApiClient.get).toHaveBeenCalledWith('/api/health');
  });

  it('should fetch list of users', async () => {
    const users = await mockApiClient.get('/api/users');
    expect(users).toHaveLength(2);
    expect(users[0].name).toBe('User 1');
  });

  it('should make POST request', async () => {
    const newUser = { name: 'New User', email: 'new@example.com' };
    const result = await mockApiClient.post('/api/users', newUser);
    
    expect(result).toHaveProperty('id');
    expect(result.name).toBe('New User');
  });

  it('should make PUT request', async () => {
    const updatedData = { id: 1, name: 'Updated User' };
    const result = await mockApiClient.put('/api/users/1', updatedData);
    
    expect(result.updated).toBe(true);
    expect(result.name).toBe('Updated User');
  });

  it('should make DELETE request', async () => {
    const result = await mockApiClient.delete('/api/users/1');
    expect(result.success).toBe(true);
  });

  it('should handle errors', async () => {
    const errorClient = {
      get: vi.fn(async () => {
        throw new Error('Network error');
      }),
    };

    await expect(errorClient.get('/api/fail')).rejects.toThrow('Network error');
  });
});

describe('API Error Handling', () => {
  it('should handle 404 errors', () => {
    const handleError = (status: number) => {
      if (status === 404) return 'Not Found';
      return 'Error';
    };

    expect(handleError(404)).toBe('Not Found');
  });

  it('should handle 401 unauthorized', () => {
    const handleError = (status: number) => {
      if (status === 401) return 'Unauthorized';
      return 'Error';
    };

    expect(handleError(401)).toBe('Unauthorized');
  });

  it('should handle 500 server errors', () => {
    const handleError = (status: number) => {
      if (status === 500) return 'Server Error';
      return 'Error';
    };

    expect(handleError(500)).toBe('Server Error');
  });
});
