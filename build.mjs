import { cp, mkdir, rm } from "node:fs/promises";

await rm("public", { recursive: true, force: true });
await mkdir("public", { recursive: true });

for (const entry of ["index.html", "styles.css", "app.js", "assets", "data"]) {
  await cp(entry, `public/${entry}`, { recursive: true });
}

console.log("Prepared static Vercel output in public/");
