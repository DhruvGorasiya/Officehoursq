import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegisterPage from '@/app/(auth)/register/page';
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

describe('RegisterPage', () => {
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

  it('renders all fields: name, email, password, role dropdown', () => {
    render(<RegisterPage />);
    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/University Email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/I am a.../i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Register/i })).toBeInTheDocument();
  });

  it('role dropdown contains exactly: student, ta, professor', () => {
    render(<RegisterPage />);
    const roleSelect = screen.getByLabelText(/I am a.../i) as HTMLSelectElement;
    
    // There should be exactly 3 options
    expect(roleSelect.options.length).toBe(3);
    
    // Convert options to an array of their values
    const options = Array.from(roleSelect.options).map(opt => opt.value);
    
    expect(options).toEqual(expect.arrayContaining(['student', 'ta', 'professor']));
    expect(options.length).toBe(3);
  });

  it('shows validation error on empty submit', () => {
    render(<RegisterPage />);
    expect(screen.getByLabelText(/Full Name/i)).toBeRequired();
    expect(screen.getByLabelText(/University Email/i)).toBeRequired();
    expect(screen.getByLabelText(/Password/i)).toBeRequired();
  });

  it('shows password length validation error without calling API', async () => {
    render(<RegisterPage />);
    
    await userEvent.type(screen.getByLabelText(/Full Name/i), 'Jane Doe');
    await userEvent.type(screen.getByLabelText(/University Email/i), 'jane@example.com');
    // Type a password that is less than 8 characters
    await userEvent.type(screen.getByLabelText(/Password/i), 'short');
    
    fireEvent.click(screen.getByRole('button', { name: /Register/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    });
    
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('successful registration creates account and redirects to dashboard', async () => {
    const mockResponse = {
      success: true,
      data: {
        token: 'new-jwt-token',
        id: '999',
        email: 'jane@example.com',
        name: 'Jane Doe',
        role: 'student',
      },
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce(mockResponse),
    });

    render(<RegisterPage />);
    
    await userEvent.type(screen.getByLabelText(/Full Name/i), 'Jane Doe');
    await userEvent.type(screen.getByLabelText(/University Email/i), 'jane@example.com');
    await userEvent.type(screen.getByLabelText(/Password/i), 'securepassword123');
    
    // Select role
    const roleSelect = screen.getByLabelText(/I am a.../i);
    await userEvent.selectOptions(roleSelect, 'student');

    fireEvent.click(screen.getByRole('button', { name: /Register/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/register'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            name: 'Jane Doe',
            email: 'jane@example.com',
            password: 'securepassword123',
            role: 'student'
          }),
        })
      );
    });

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('new-jwt-token', {
        id: '999',
        email: 'jane@example.com',
        name: 'Jane Doe',
        role: 'student',
      });
      expect(mockPush).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('shows error message when API returns failure', async () => {
    const mockResponse = {
      success: false,
      message: 'Email already exists',
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: jest.fn().mockResolvedValueOnce(mockResponse),
    });

    render(<RegisterPage />);
    
    await userEvent.type(screen.getByLabelText(/Full Name/i), 'Jane Doe');
    await userEvent.type(screen.getByLabelText(/University Email/i), 'jane@example.com');
    await userEvent.type(screen.getByLabelText(/Password/i), 'validpass123');
    
    fireEvent.click(screen.getByRole('button', { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
    
    expect(mockLogin).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('shows fallback error message when fetch fails catastrophically', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<RegisterPage />);
    
    await userEvent.type(screen.getByLabelText(/Full Name/i), 'Jane Doe');
    await userEvent.type(screen.getByLabelText(/University Email/i), 'jane@example.com');
    await userEvent.type(screen.getByLabelText(/Password/i), 'validpass123');
    
    fireEvent.click(screen.getByRole('button', { name: /Register/i }));

    await waitFor(() => {
      expect(screen.getByText('A network error occurred. Please try again later.')).toBeInTheDocument();
    });
  });
});
