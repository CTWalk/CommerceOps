import {
  expect,
  test as base,
  type ConsoleMessage,
  type Page,
  type Request,
  type Response,
  type TestInfo,
} from '@playwright/test';
import { writeFile } from 'node:fs/promises';

export { expect };
export type { Page, TestInfo } from '@playwright/test';

const SENSITIVE_KEY = /password|authorization|cookie|token|secret|api[-_]?key|card(?:number|cvc|expiry)?|cvv|cvc/i;

function redactText(value: string): string {
  return value
    .replace(/\bBearer\s+[A-Za-z0-9._~+/-]+=*/gi, 'Bearer [REDACTED]')
    .replace(/(["']?(?:password|authorization|cookie|token|secret|api[-_]?key|card(?:number|cvc|expiry)?|cvv|cvc)["']?\s*[:=]\s*["']?)([^"',\s;}]+)/gi, '$1[REDACTED]')
    .replace(/\b(?:\d[ -]?){11,18}\d\b/g, '[REDACTED_CARD]');
}

function redactUrl(value: string): string {
  try {
    const url = new URL(value);
    if (url.username) url.username = '[REDACTED]';
    if (url.password) url.password = '[REDACTED]';
    for (const key of url.searchParams.keys()) {
      if (SENSITIVE_KEY.test(key)) url.searchParams.set(key, '[REDACTED]');
    }
    return url.toString();
  } catch {
    return redactText(value);
  }
}

function redact(value: unknown, key = ''): unknown {
  if (SENSITIVE_KEY.test(key)) return '[REDACTED]';
  if (typeof value === 'string') return redactText(value);
  if (Array.isArray(value)) return value.map((item) => redact(item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([entryKey, entryValue]) => [entryKey, redact(entryValue, entryKey)]));
  }
  return value;
}

function isApiRequest(value: string): boolean {
  try {
    return new URL(value).pathname.startsWith('/api/');
  } catch {
    return value.includes('/api/');
  }
}

async function attachJson(testInfo: TestInfo, name: string, value: unknown) {
  const path = testInfo.outputPath(name);
  await writeFile(path, JSON.stringify(value, null, 2));
  await testInfo.attach(name, {
    path,
    contentType: 'application/json',
  });
}

type Diagnostics = {
  consoleErrors: unknown[];
  pageErrors: unknown[];
  failedApiRequests: unknown[];
  onConsole: (message: ConsoleMessage) => void;
  onPageError: (error: Error) => void;
  onRequestFailed: (request: Request) => void;
  onResponse: (response: Response) => void;
};

const diagnosticsByPage = new WeakMap<Page, Diagnostics>();

export const test = base;

export function startFailureDiagnostics(page: Page, _testInfo: TestInfo) {
  const consoleErrors: unknown[] = [];
  const pageErrors: unknown[] = [];
  const failedApiRequests: unknown[] = [];
  const diagnostics: Diagnostics = {
    consoleErrors,
    pageErrors,
    failedApiRequests,
    onConsole: (message) => {
      if (message.type() !== 'error') return;
      const location = message.location();
      consoleErrors.push({
        text: redactText(message.text()),
        location: { url: redactUrl(location.url), line: location.lineNumber, column: location.columnNumber },
      });
    },
    onPageError: (error) => pageErrors.push({
      message: redactText(error.message),
      stack: error.stack ? redactText(error.stack) : undefined,
    }),
    onRequestFailed: (request) => {
      if (!isApiRequest(request.url())) return;
      failedApiRequests.push({
        kind: 'network', method: request.method(), url: redactUrl(request.url()),
        error: redactText(request.failure()?.errorText || 'Unknown network error'),
      });
    },
    onResponse: (response) => {
      if (response.status() < 400 || !isApiRequest(response.url())) return;
      failedApiRequests.push({
        kind: 'http', method: response.request().method(), url: redactUrl(response.url()),
        status: response.status(), statusText: redactText(response.statusText()),
      });
    },
  };
  diagnosticsByPage.set(page, diagnostics);
  page.on('console', diagnostics.onConsole);
  page.on('pageerror', diagnostics.onPageError);
  page.on('requestfailed', diagnostics.onRequestFailed);
  page.on('response', diagnostics.onResponse);
}

export async function finishFailureDiagnostics(page: Page, testInfo: TestInfo) {
  const diagnostics = diagnosticsByPage.get(page);
  if (!diagnostics) {
    await testInfo.attach('failure-evidence-error.txt', {
      body: 'Browser diagnostics were not initialized for this test.',
      contentType: 'text/plain',
    });
    return;
  }
  try {
    await attachJson(testInfo, 'browser-diagnostics.json', {
      capturedAt: new Date().toISOString(),
      test: {
        title: testInfo.title,
        file: testInfo.file,
        retry: testInfo.retry,
        errors: testInfo.errors.map((error) => redactText(error.stack || error.message)),
      },
      consoleErrors: diagnostics.consoleErrors,
      pageErrors: diagnostics.pageErrors,
      failedApiRequests: diagnostics.failedApiRequests,
    });
    const response = await page.request.get('/api/events', { timeout: 5_000 });
    const body = await response.json();
    await attachJson(testInfo, 'api-events.json', {
      capturedAt: new Date().toISOString(),
      status: response.status(),
      events: redact(body.events),
    });
  } catch (error) {
    await testInfo.attach('failure-evidence-error.txt', {
      body: redactText(error instanceof Error ? error.stack || error.message : String(error)),
      contentType: 'text/plain',
    }).catch(() => undefined);
  } finally {
    page.off('console', diagnostics.onConsole);
    page.off('pageerror', diagnostics.onPageError);
    page.off('requestfailed', diagnostics.onRequestFailed);
    page.off('response', diagnostics.onResponse);
    diagnosticsByPage.delete(page);
  }
}
