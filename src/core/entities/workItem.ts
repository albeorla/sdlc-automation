export enum WorkItemStatus {
  DRAFT = 'draft',
  READY = 'ready',
  IN_PROGRESS = 'in_progress',
  REVIEW = 'review',
  DONE = 'done'
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface WorkItem {
  id: string;
  title: string;
  description: string;
  status: WorkItemStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface Epic extends WorkItem {
  type: 'epic';
  businessValue: string;
  strategicAlignment: string;
  successMetrics: string[];
  scope: string[];
  roadmapReference?: string;
}

export interface Story extends WorkItem {
  type: 'story';
  epicId: string;
  acceptanceCriteria: string[];
  priority: Priority;
}

export interface Task extends WorkItem {
  type: 'task';
  storyId: string;
  assignee?: string;
  estimatedEffort: number;
  relatedFiles: string[];
}
