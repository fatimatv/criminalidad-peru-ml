import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const dist = join(root, "dist");

if (existsSync(dist)) {
  rmSync(dist, { recursive: true, force: true });
}

mkdirSync(dist, { recursive: true });

const files = [
  "index.html",
  "README.md",
  "DECISIONS.md",
  "rubric_compliance.md",
  "requirements.txt",
];

const directories = [
  "report",
  "presentation",
  "notebooks",
  "defense",
  "references",
  "assets",
  "outputs/figures",
  "outputs/tables",
  "data/processed",
  "data/geo",
];

for (const file of files) {
  if (existsSync(join(root, file))) {
    cpSync(join(root, file), join(dist, file));
  }
}

for (const directory of directories) {
  const source = join(root, directory);
  if (existsSync(source)) {
    cpSync(source, join(dist, directory), { recursive: true });
  }
}
