import { readFile } from "node:fs/promises";
import { readdirSync } from "node:fs";
import path from "node:path";

export async function buildAcademyPackage(root = process.cwd()) {
  const coursesRoot = path.join(root, "learning", "courses");
  const courses = [];

  for (const entry of readdirSync(coursesRoot, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (!entry.isDirectory()) {
      continue;
    }
    const coursePath = path.join(coursesRoot, entry.name, "course.json");
    const course = await readJson(coursePath);
    const lessonData = [];
    for (const lessonId of course.lessons ?? []) {
      const lessonPath = path.join(coursesRoot, entry.name, "lessons", `${lessonId}.json`);
      lessonData.push(await readJson(lessonPath));
    }
    courses.push({ ...course, lessonData });
  }

  return {
    schemaVersion: 1,
    packageId: "freak-academy-v3-mvp",
    languageVersion: "0.13.3",
    compilerTrack: "v3",
    repositoryPhase: "main-repo",
    websiteConnector: "freaklang.dev",
    workerProtocolVersion: 1,
    courses,
  };
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}
