import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
const requireWeb = createRequire(
  new URL("../apps/web/package.json", import.meta.url),
);
const { createLibrary, defineComponent, createParser } = requireWeb(
  "@openuidev/react-lang",
);
const { z } = requireWeb("zod/v4");
const catalogPath = new URL(
  "../protocol/intelligent-ui-catalog.json",
  import.meta.url,
);
const catalog = JSON.parse(readFileSync(catalogPath, "utf8"));
const components = Object.entries(catalog.components).map(
  ([name, description]) =>
    defineComponent({
      name,
      description,
      props: z.object({ evidence_ref: z.string() }),
      component: () => null,
    }),
);
const root = defineComponent({
  name: catalog.root,
  description:
    "Bounded learning interactions below an independently readable answer.",
  props: z.object({ children: z.array(z.union(components.map((c) => c.ref))) }),
  component: () => null,
});
const library = createLibrary({
  root: catalog.root,
  components: [root, ...components],
});
const prompt = library.prompt();
const out = new URL("../protocol/intelligent-ui-prompt.txt", import.meta.url);
if (process.argv.includes("--check")) {
  if (readFileSync(out, "utf8") !== prompt)
    throw Error(
      "OpenUI catalog prompt is stale. Run npm run generate:ui-catalog.",
    );
} else writeFileSync(out, prompt);
// SDK conformance gate for the exact language compiled by the server.
const sample =
  'root = LearningUI([c0, c1])\nc0 = ConditionChecklist("claim:current")\nc1 = SourceExcerpt("claim:current")';
const result = createParser(library.toJSONSchema()).parse(sample);
if (
  result.meta?.errors?.length ||
  result.meta?.unresolved?.length ||
  !result.root
)
  throw Error(
    "OpenUI SDK rejected the catalog sample: " + JSON.stringify(result.meta),
  );
console.log(
  `Verified ${catalog.version}, ${catalog.sdk}, ${components.length} components: ${fileURLToPath(out)}`,
);
