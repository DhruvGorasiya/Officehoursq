import React from 'react';
import { render, screen } from '@testing-library/react';
import NavBar from '@/components/common/NavBar';
import { useAuth } from '@/context/AuthContext';

// Mock Next.js Link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode, href: string }) => {
    return <a href={href}>{children}</a>;
  };
});

// Mock AuthContext
jest.mock('@/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

describe('NavBar', () => {
  const mockLogout = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders course name correctly', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: null,
      logout: mockLogout,
      unreadCount: 0,
    });

    render(<NavBar title="CS 101" />);
    expect(screen.getByText('CS 101')).toBeInTheDocument();
  });

  it('shows notification bell with red badge when unread count > 0', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: null,
      logout: mockLogout,
      unreadCount: 3,
    });

    render(<NavBar title="Test Course" />);
    // The badge with "3" should be rendered
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('hides badge when count is 0', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: null,
      logout: mockLogout,
      unreadCount: 0,
    });

    render(<NavBar title="Test Course" />);
    // There shouldn't be any badge rendering '0'
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('shows correct user initials in avatar', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: { name: 'John Doe', email: 'john@example.com', role: 'student', id: '1' },
      logout: mockLogout,
      unreadCount: 0,
    });

    render(<NavBar title="Test Course" />);
    // "John Doe" -> "JD"
    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('shows Sign In when user is not logged in', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: null,
      logout: mockLogout,
      unreadCount: 0,
    });

    render(<NavBar title="Test Course" />);
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });
});
