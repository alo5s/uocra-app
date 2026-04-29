const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const baseUrl = 'http://localhost:5174';
  const screenshotsDir = '/home/alos/Mio/version estable/uocra-app_app otra version/screenshots';

  // 1. Login page screenshot
  console.log('1. Taking screenshot: login.png');
  await page.goto(baseUrl + '/login', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: screenshotsDir + '/login.png', fullPage: true });

  // Login
  console.log('2. Logging in...');
  await page.fill('input[type="text"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/home', { timeout: 10000 });
  console.log('Login successful');
  await page.waitForTimeout(3000);

  // 2. Dashboard screenshot (already on /home)
  console.log('3. Taking screenshot: dashboard.png');
  await page.screenshot({ path: screenshotsDir + '/dashboard.png', fullPage: true });

  // 3. Navigate to CVs by clicking sidebar link (no page reload)
  console.log('4. Navigating to CVs...');
  await page.click('a[href="/cvs"]');
  await page.waitForTimeout(3000);
  console.log('URL after clicking CVs:', page.url());
  await page.screenshot({ path: screenshotsDir + '/cvs.png', fullPage: true });

  // 4. Navigate to Nuevo CV by clicking
  console.log('5. Navigating to Nuevo CV...');
  await page.click('a[href="/cv/nuevo"]');
  await page.waitForTimeout(3000);
  console.log('URL after clicking Nuevo CV:', page.url());
  await page.screenshot({ path: screenshotsDir + '/cvs-nuevo.png', fullPage: true });

  // 5. Navigate to Empresas by clicking sidebar link
  console.log('6. Navigating to Empresas...');
  await page.click('a[href="/empresas"]');
  await page.waitForTimeout(3000);
  console.log('URL after clicking Empresas:', page.url());
  await page.screenshot({ path: screenshotsDir + '/empresas.png', fullPage: true });

  // 6. Navigate to Notas by clicking sidebar link
  console.log('7. Navigating to Notas...');
  await page.click('a[href="/notas"]');
  await page.waitForTimeout(3000);
  console.log('URL after clicking Notas:', page.url());
  await page.screenshot({ path: screenshotsDir + '/notas.png', fullPage: true });

  // 7. Navigate to Actividad by clicking sidebar link (admin only)
  console.log('8. Navigating to Actividad...');
  await page.click('a[href="/actividad"]');
  await page.waitForTimeout(3000);
  console.log('URL after clicking Actividad:', page.url());
  await page.screenshot({ path: screenshotsDir + '/actividad.png', fullPage: true });

  // 8. Public QR page (no auth needed, can use goto)
  console.log('9. Taking screenshot: bienvenido.png');
  await page.goto(baseUrl + '/cv/qr', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: screenshotsDir + '/bienvenido.png', fullPage: true });

  console.log('All screenshots taken successfully!');
  await browser.close();
})();
