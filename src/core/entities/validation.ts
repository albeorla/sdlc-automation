export interface Commit {
  hash: string;
  message: string;
  author: string;
  date: Date;
  files: string[];
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  code: string;
  message: string;
  location?: string;
}

export interface ValidationWarning {
  code: string;
  message: string;
  location?: string;
}

export interface ReviewResult {
  issues: ReviewIssue[];
  suggestions: ReviewSuggestion[];
}

export interface ReviewIssue {
  file: string;
  line?: number;
  issueType: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
}

export interface ReviewSuggestion {
  file: string;
  line?: number;
  message: string;
}
