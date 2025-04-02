import { GitProvider } from '../../core/interfaces/repository';
import { Commit } from '../../core/entities/validation';
import { IntegrationError } from '../../core/errors';
import simpleGit, { SimpleGit } from 'simple-git';

export class GitAdapter implements GitProvider {
  private git: SimpleGit;

  constructor(private repoPath: string) {
    this.git = simpleGit(repoPath);
  }

  async getCommits(since: string, until: string): Promise<Commit[]> {
    try {
      const logResult = await this.git.log({ from: since, to: until });
      
      return logResult.all.map(commit => ({
        hash: commit.hash,
        message: commit.message,
        author: commit.author_name,
        date: new Date(commit.date),
        files: []
      }));
    } catch (error) {
      throw new IntegrationError(`Failed to get commits: ${error.message}`);
    }
  }

  async getChangedFiles(since: string, until: string): Promise<string[]> {
    try {
      const diffResult = await this.git.diff([`${since}...${until}`, '--name-only']);
      return diffResult.split('\n').filter(file => file.trim() !== '');
    } catch (error) {
      throw new IntegrationError(`Failed to get changed files: ${error.message}`);
    }
  }

  async getCommitMessage(commitHash: string): Promise<string> {
    try {
      const showResult = await this.git.show([commitHash, '--pretty=%B', '--no-patch']);
      return showResult.trim();
    } catch (error) {
      throw new IntegrationError(`Failed to get commit message: ${error.message}`);
    }
  }
}
