const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface HealthCheckResponse {
  status: string;
  environment: string;
}

export interface SessionResponse {
  sessionId: string;
  createdAt: string;
  expiresAt: string;
  status: string;
}

export interface SessionStatusResponse {
  sessionId: string;
  status: string;
  errorMessage: string | null;
  updatedAt: string | null;
}

export interface Transaction {
  id: string;
  sessionId: string;
  date: string;
  rawDescription: string;
  cleanDescription: string;
  merchant: string | null;
  amount: number;
  type: 'debit' | 'credit';
  category: string;
  categoryConfidence: number;
  categorySource: string;
  isRecurring: boolean;
  recurringGroupId: string | null;
}

export interface PaginatedTransactions {
  transactions: Transaction[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface RecurringGroup {
  groupId: string;
  merchant: string | null;
  description: string;
  amount: number;
  frequency: 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  type: 'subscription' | 'emi' | 'rent' | 'sip' | 'insurance' | 'other';
  transactions: {
    id: string;
    date: string;
    rawDescription: string;
    cleanDescription: string;
    merchant: string | null;
    amount: number;
    type: 'debit' | 'credit';
    category: string;
  }[];
}

export interface SummaryResponse {
  income: number;
  spend: number;
  savings: number;
  savingsRate: number;
  biggestTransaction: {
    id: string;
    date: string;
    description: string;
    merchant: string | null;
    amount: number;
    category: string;
  } | null;
  topCategories: {
    category: string;
    amount: number;
    percentage: number;
  }[];
  monthlyAggregation: {
    month: string;
    income: number;
    spend: number;
  }[];
  recurringTotal: number;
}

export interface Insight {
  id: string;
  type: string;
  title: string;
  text: string;
  amount: number | null;
  relevance: number;
}

export const api = {
  /**
   * Check the health of the backend API
   */
  async checkHealth(): Promise<HealthCheckResponse> {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });
    
    if (!response.ok) {
      throw new Error(`API health check failed with status: ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * Create a new ephemeral session
   */
  async createSession(): Promise<SessionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to create session');
    }

    return response.json();
  },

  /**
   * Check status of a session
   */
  async getSessionStatus(sessionId: string): Promise<SessionStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/status`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const err = new Error(errData.detail || `Failed to fetch session status for: ${sessionId}`);
      (err as any).status = response.status;
      throw err;
    }

    return response.json();
  },

  /**
   * Delete a session and its data
   */
  async deleteSession(sessionId: string): Promise<{ status: string; sessionId: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to delete session: ${sessionId}`);
    }

    return response.json();
  },

  /**
   * Upload a bank statement file (CSV)
   */
  async uploadStatement(sessionId: string, file: File): Promise<{
    sessionId: string;
    filename: string;
    sizeBytes: number;
    message: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/upload`, {
      method: 'POST',
      body: formData,
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to upload statement file');
    }

    return response.json();
  },

  /**
   * Trigger statement analysis pipeline
   */
  async analyzeSession(
    sessionId: string,
    columnMapping?: Record<string, string>
  ): Promise<{
    status: string;
    sessionId: string;
    summary: {
      total_parsed: number;
      valid_extracted: number;
      skipped: number;
      duplicates_removed: number;
      column_mapping: Record<string, string>;
    };
  }> {
    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    if (columnMapping) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/analyze`, {
      method: 'POST',
      headers,
      body: columnMapping ? JSON.stringify(columnMapping) : undefined,
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const errMsg = typeof errData.detail === 'object' ? (errData.detail.message || 'Pipeline analysis failed') : (errData.detail || 'Pipeline analysis failed');
      const err = new Error(errMsg);
      if (errData.detail && typeof errData.detail === 'object') {
        (err as any).detail = errData.detail;
      }
      throw err;
    }

    return response.json();
  },

  /**
   * Fetch paginated and filtered transactions
   */
  async getTransactions(
    sessionId: string,
    page = 1,
    limit = 50,
    category?: string,
    search?: string,
    fromDate?: string,
    toDate?: string
  ): Promise<PaginatedTransactions> {
    let url = `${API_BASE_URL}/api/v1/sessions/${sessionId}/transactions?page=${page}&limit=${limit}`;
    if (category) {
      url += `&category=${encodeURIComponent(category)}`;
    }
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    if (fromDate) {
      url += `&fromDate=${encodeURIComponent(fromDate)}`;
    }
    if (toDate) {
      url += `&toDate=${encodeURIComponent(toDate)}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to fetch transactions');
    }

    return response.json();
  },

  /**
   * Fetch recurring transaction groups
   */
  async getRecurring(sessionId: string): Promise<RecurringGroup[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/recurring`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to fetch recurring transactions');
    }

    return response.json();
  },

  /**
   * Fetch financial summary metrics
   */
  async getSummary(sessionId: string, fromDate?: string, toDate?: string): Promise<SummaryResponse> {
    let url = `${API_BASE_URL}/api/v1/sessions/${sessionId}/summary`;
    const params = new URLSearchParams();
    if (fromDate) params.append('fromDate', fromDate);
    if (toDate) params.append('toDate', toDate);
    
    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to fetch financial summary');
    }

    return response.json();
  },

  /**
   * Fetch financial insights
   */
  async getInsights(sessionId: string): Promise<Insight[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/insights`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to fetch financial insights');
    }

    return response.json();
  },

  /**
   * Manually override a transaction's category and learn a rule for the session
   */
  async overrideCategory(
    sessionId: string,
    txId: string,
    category: string
  ): Promise<{
    status: string;
    message: string;
    transactionId: string;
    updatedCount: number;
  }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/sessions/${sessionId}/transactions/${txId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ category }),
      cache: 'no-store'
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to override category');
    }

    return response.json();
  }
};
