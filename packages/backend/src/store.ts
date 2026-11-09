/**
 * Project/component persistence.
 *
 * Default: JSON file store (atomic writes) — zero native dependencies,
 * works everywhere. The interface is storage-agnostic: a SQLite
 * (node:sqlite) or PostgreSQL implementation can replace FileStore
 * without changing routes. See docs/ARCHITECTURE.md.
 */
import { readFileSync, writeFileSync, renameSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { Project, ParametricComponent, seedLibrary } from '@horology/engineering-core';

export interface Store {
  listProjects(): Project[];
  getProject(id: string): Project | undefined;
  saveProject(p: Project): Project;
  deleteProject(id: string): boolean;
  listComponents(): ParametricComponent[];
  getComponent(id: string): ParametricComponent | undefined;
  saveComponent(c: ParametricComponent): ParametricComponent;
  deleteComponent(id: string): boolean;
}

export class FileStore implements Store {
  private dir: string;
  private projectsFile: string;
  private componentsFile: string;
  private projects = new Map<string, Project>();
  private components = new Map<string, ParametricComponent>();

  constructor(dir = process.env.HOROLOGY_DATA_DIR ?? join(process.cwd(), 'data')) {
    this.dir = dir;
    this.projectsFile = join(dir, 'projects.json');
    this.componentsFile = join(dir, 'components.json');
    mkdirSync(dir, { recursive: true });
    this.load();
  }

  private load() {
    if (existsSync(this.projectsFile)) {
      try {
        const arr = JSON.parse(readFileSync(this.projectsFile, 'utf8')) as Project[];
        for (const p of arr) this.projects.set(p.id, p);
      } catch { /* corrupted file: start empty, do not crash */ }
    }
    if (existsSync(this.componentsFile)) {
      try {
        const arr = JSON.parse(readFileSync(this.componentsFile, 'utf8')) as ParametricComponent[];
        for (const c of arr) this.components.set(c.id, c);
      } catch { /* ignore */ }
    }
    if (this.components.size === 0) {
      for (const c of seedLibrary().list()) this.components.set(c.id, c);
      this.persistComponents();
    }
  }

  private persistProjects() {
    const tmp = `${this.projectsFile}.tmp`;
    writeFileSync(tmp, JSON.stringify([...this.projects.values()], null, 2));
    renameSync(tmp, this.projectsFile);
  }
  private persistComponents() {
    const tmp = `${this.componentsFile}.tmp`;
    writeFileSync(tmp, JSON.stringify([...this.components.values()], null, 2));
    renameSync(tmp, this.componentsFile);
  }

  listProjects() { return [...this.projects.values()]; }
  getProject(id: string) { return this.projects.get(id); }
  saveProject(p: Project) { this.projects.set(p.id, p); this.persistProjects(); return p; }
  deleteProject(id: string) { const ok = this.projects.delete(id); if (ok) this.persistProjects(); return ok; }
  listComponents() { return [...this.components.values()]; }
  getComponent(id: string) { return this.components.get(id); }
  saveComponent(c: ParametricComponent) { this.components.set(c.id, c); this.persistComponents(); return c; }
  deleteComponent(id: string) { const ok = this.components.delete(id); if (ok) this.persistComponents(); return ok; }
}

export function createStore(): Store {
  return new FileStore();
}
