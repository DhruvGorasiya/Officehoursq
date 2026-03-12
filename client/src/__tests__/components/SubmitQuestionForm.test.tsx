import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import QuestionSubmissionForm from '@/components/questions/QuestionSubmissionForm';
import { useAuth } from '@/context/AuthContext';
import * as kbApi from '@/lib/knowledgeBaseApi';

jest.mock('@/context/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock knowledge base API
jest.mock('@/lib/knowledgeBaseApi', () => ({
  fetchSimilarQuestions: jest.fn(),
}));

describe('QuestionSubmissionForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({
      token: 'fake-token',
    });
    (kbApi.fetchSimilarQuestions as jest.Mock).mockResolvedValue({
      success: true,
      data: [{ id: '1', title: 'Similar issue', resolved_at: '2024-01-01' }]
    });
  });

  it('renders all required fields', () => {
    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={jest.fn()} 
        activeQuestion={null} 
        onWithdraw={jest.fn()} 
        courseId="course-1" 
      />
    );

    // Using exact label matching string interpolation to parse Next lines
    expect(screen.getByText(/Title/)).toBeInTheDocument();
    expect(screen.getByText(/Description/)).toBeInTheDocument();
    expect(screen.getByText(/What I've Tried/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Submit Question' })).toBeInTheDocument();
  });

  it('similar questions panel does not appear when title < 5 chars', async () => {
    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={jest.fn()} 
        activeQuestion={null} 
        onWithdraw={jest.fn()} 
        courseId="course-1" 
      />
    );

    const titleInput = screen.getByPlaceholderText(/Brief summary of your issue/);
    
    // Type 4 characters
    await userEvent.type(titleInput, 'abcd');
    
    // Wait for the debounce buffer time (400ms) within act
    await act(async () => {
      await new Promise(r => setTimeout(r, 450));
    });
    
    expect(kbApi.fetchSimilarQuestions).not.toHaveBeenCalled();
    expect(screen.queryByText(/Similar issue/)).not.toBeInTheDocument();
  });

  it('similar questions panel appears when title > 5 chars', async () => {
    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={jest.fn()} 
        activeQuestion={null} 
        onWithdraw={jest.fn()} 
        courseId="course-1" 
      />
    );

    const titleInput = screen.getByPlaceholderText(/Brief summary of your issue/);
    
    // Type 6 characters
    await userEvent.type(titleInput, 'abcdef');
    
    // Wait for the debounce buffer time (400ms) and rerenders
    await waitFor(() => {
      expect(kbApi.fetchSimilarQuestions).toHaveBeenCalledWith({
        courseId: 'course-1',
        title: 'abcdef',
        token: 'fake-token',
      });
    }, { timeout: 1000 });

    await waitFor(() => {
      expect(screen.getByText('Similar issue')).toBeInTheDocument();
    });
  });

  it('submits form successfully with all required and optional fields', async () => {
    // Mock successful submission
    const mockFetch = jest.fn().mockResolvedValue({
      json: jest.fn().mockResolvedValue({ success: true })
    });
    global.fetch = mockFetch;

    const onSuccessMock = jest.fn();

    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={onSuccessMock} 
        activeQuestion={null} 
        onWithdraw={jest.fn()} 
        courseId="course-1" 
      />
    );

    await userEvent.type(screen.getByLabelText(/Title/i), 'How does useEffect work?');
    await userEvent.type(screen.getByLabelText(/Description/i), 'I am getting an infinite loop');
    await userEvent.type(screen.getByLabelText(/What I've Tried/i), 'I read the React docs');
    await userEvent.type(screen.getByLabelText(/Code Snippet/i), 'useEffect(() => setCount(count + 1))');
    await userEvent.type(screen.getByLabelText(/Error Message/i), 'Maximum update depth exceeded');

    // Change dropdowns
    const categorySelect = screen.getByLabelText(/Category/i);
    await userEvent.selectOptions(categorySelect, 'conceptual');
    
    const prioritySelect = screen.getByLabelText(/Priority/i);
    await userEvent.selectOptions(prioritySelect, 'high');

    // Submit form
    const submitButton = screen.getByRole('button', { name: 'Submit Question' });
    
    // Wrap in act for React state updates
    await act(async () => {
      submitButton.click();
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/questions'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            Authorization: 'Bearer fake-token'
          }),
          body: JSON.stringify({
            session_id: 'sess-1',
            title: 'How does useEffect work?',
            description: 'I am getting an infinite loop',
            code_snippet: 'useEffect(() => setCount(count + 1))',
            error_message: 'Maximum update depth exceeded',
            what_tried: 'I read the React docs',
            category: 'conceptual',
            priority: 'high'
          })
        })
      );
    });

    expect(onSuccessMock).toHaveBeenCalled();
  });

  it('shows error state when missing required fields (browser validation prevents submit but we test input required props)', () => {
    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={jest.fn()} 
        activeQuestion={null} 
        onWithdraw={jest.fn()} 
        courseId="course-1" 
      />
    );

    expect(screen.getByLabelText(/Title/i)).toBeRequired();
    expect(screen.getByLabelText(/Description/i)).toBeRequired();
    expect(screen.getByLabelText(/What I've Tried/i)).toBeRequired();
  });

  it('renders queue status view when activeQuestion is provided', () => {
    const mockQuestion = {
      id: 'q-123',
      title: 'Queue status test title',
      description: 'Waiting in line',
      status: 'queued',
      category: 'debugging',
      priority: 'high',
      queue_position: 3,
      estimated_wait_minutes: 15
    };

    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={jest.fn()} 
        activeQuestion={mockQuestion} 
        onWithdraw={jest.fn()} 
        courseId="course-1" 
      />
    );

    expect(screen.getByText('Queue Status')).toBeInTheDocument();
    expect(screen.getByText('Queue status test title')).toBeInTheDocument();
    expect(screen.getByText('Waiting in line')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Queue position
    expect(screen.getByText(/Estimated wait: ~15 min/i)).toBeInTheDocument();
    expect(screen.getByText(/high priority/i)).toBeInTheDocument();
    expect(screen.getByText('debugging')).toBeInTheDocument();
  });

  it('calls onWithdraw when withdraw button is clicked in queue status', async () => {
    const mockQuestion = {
      id: 'q-123',
      title: 'Queue status test title',
      description: 'Waiting in line',
      status: 'queued',
      queue_position: 3
    };

    const mockWithdraw = jest.fn();

    render(
      <QuestionSubmissionForm 
        sessionId="sess-1" 
        onSuccess={jest.fn()} 
        activeQuestion={mockQuestion} 
        onWithdraw={mockWithdraw} 
        courseId="course-1" 
      />
    );

    const withdrawBtn = screen.getByRole('button', { name: /Withdraw/i });
    
    await act(async () => {
      withdrawBtn.click();
    });

    expect(mockWithdraw).toHaveBeenCalledWith('q-123');
  });
});
