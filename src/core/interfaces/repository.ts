import { WorkItem, Epic, Story, Task } from '../entities/workItem';
import { ValidationResult } from '../entities/validation';

export interface Repository<T> {
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<T>;
  update(id: string, entity: Partial<T>): Promise<T>;
  delete(id: string): Promise<boolean>;
}

export interface WorkItemRepository extends Repository<WorkItem> {
  findByType(type: string): Promise<WorkItem[]>;
  findByStatus(status: string): Promise<WorkItem[]>;
  findChildren(parentId: string): Promise<WorkItem[]>;
}

export interface RoadmapRepository extends Repository<RoadmapItem> {
  findByTimeframe(timeframe: string): Promise<RoadmapItem[]>;
}

export interface GitProvider {
  getCommits(since: string, until: string): Promise<Commit[]>;
  getChangedFiles(since: string, until: string): Promise<string[]>;
  getCommitMessage(commitHash: string): Promise<string>;
}

export interface Validator<T> {
  validate(input: T): ValidationResult;
}

export interface WorkItemService {
  createEpic(epicData: Partial<Epic>): Promise<Epic>;
  createStoriesFromEpic(epicId: string): Promise<Story[]>;
  createTasksFromStory(storyId: string): Promise<Task[]>;
  updateTaskWithFiles(taskId: string, files: string[]): Promise<Task>;
}

export interface DocumentationService {
  checkUpdatesNeeded(changedFiles: string[]): Promise<string[]>;
  generateReleaseNotes(fromRef: string, toRef: string, version: string): Promise<string>;
}

export interface CodeAnalysisService {
  validateCommitMessage(message: string): Promise<ValidationResult>;
  reviewPullRequest(baseRef: string, headRef: string): Promise<ReviewResult>;
  checkArchitecturalPatterns(files: string[]): Promise<ValidationResult>;
}

// Import missing types
import { RoadmapItem } from '../entities/roadmapItem';
import { Commit, ReviewResult } from '../entities/validation';
