import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from '@/app/(auth)/login/page';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode, href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

jest.mock('@/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock fetch globally
global.fetch = jest.fn();

describe('LoginPage', () => {
  const mockLogin = jest.fn();
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      login: mockLogin,
    });
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  it('renders email, password fields and submit button', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  it('shows validation error when submitted empty (handled by browser naturally, but verifying inputs are required)', () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/Email/i)).toBeRequired();
    expect(screen.getByLabelText(/Password/i)).toBeRequired();
  });

  it('calls the login API function on valid input', async () => {
    const mockReponse = {
      success: true,
      data: {
        token: 'fake-jwt-token',
        id: '123',
        email: 'test@example.com',
        name: 'Test Student',
        role: 'student',
      },
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce(mockReponse),
    });

    render(<LoginPage />);
    
    await userEvent.type(screen.getByLabelText(/Email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/Password/i), 'password123');
    
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'test@example.com', password: 'password123' }),
        })
      );
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('fake-jwt-token', {
        id: '123',
        email: 'test@example.com',
        name: 'Test Student',
        role: 'student',
      });
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('shows error message when API returns failure', async () => {
    const mockReponse = {
      success: false,
      message: 'Invalid credentials',
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce(mockReponse),
    });

    render(<LoginPage />);
    
    await userEvent.type(screen.getByLabelText(/Email/i), 'wrong@example.com');
    await userEvent.type(screen.getByLabelText(/Password/i), 'wrongpass');
    
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
    
    // Make sure login Context function was never called
    expect(mockLogin).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });
});
