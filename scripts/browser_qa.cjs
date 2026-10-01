const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('assert');
(async()=>{
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH || undefined,args:['--no-sandbox']});
const first=await browser.newContext({geolocation:{latitude:-34.901,longitude:-56.165},permissions:['geolocation']});
const second=await browser.newContext(); const a=await first.newPage(), b=await second.newPage(); const errors=[]; a.on('pageerror',e=>errors.push(e.message));
await Promise.all([a.goto('http://127.0.0.1:5000'),b.goto('http://127.0.0.1:5000')]);
await a.waitForFunction(()=>!!window.L); await a.waitForTimeout(1500);
for(const width of [360,375,390,430,768,1024,1440]){await a.setViewportSize({width,height:900}); assert(await a.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width}`); await a.locator('#report').click(); assert(await a.locator('#report-dialog').evaluate(e=>e.scrollWidth<=e.clientWidth),`dialog ${width}`); await a.locator('#close').click()}
await a.setViewportSize({width:390,height:844}); await a.locator('#report').click();
await a.locator('#locate').click(); await a.waitForFunction(()=>document.querySelector('[name=latitude]').value==='-34.901');
await a.locator('#picker').click({position:{x:100,y:100}}); assert(await a.locator('[name=latitude]').inputValue());
await a.locator('[name=title]').fill('PRUEBA QA temporal'); await a.locator('textarea[name=description]').fill('Reporte de prueba en base aislada, se eliminará.');
await a.locator('#submit').click(); await a.locator('#success').waitFor({state:'visible'}); const privateUrl=await a.locator('#private-link').inputValue();
await b.waitForFunction(()=>document.querySelector('#reports').textContent.includes('PRUEBA QA temporal'),{},{timeout:18000});
await a.locator('#close-success').click(); await a.goto(privateUrl); await a.locator('#delete').click();
await a.waitForFunction(()=>document.querySelector('#delete-message').textContent.includes('Alerta eliminada'));
await b.waitForFunction(()=>!document.querySelector('#reports').textContent.includes('PRUEBA QA temporal'),{},{timeout:18000});
await b.locator('#report').click(); await b.locator('#locate').click(); await b.waitForFunction(()=>document.querySelector('#location-message').textContent.includes('No pudimos'),{},{timeout:12000}); await b.locator('#close').click();
await b.locator('#report').click(); await b.locator('[name=title]').fill('Formulario conservado'); await b.locator('textarea[name=description]').fill('Prueba de fallo de conexión'); await b.locator('[name=latitude]').fill('-34.9'); await b.locator('[name=longitude]').fill('-56.1');
await b.route('**/api/reports', route => route.abort()); await b.locator('#submit').click(); await b.waitForFunction(()=>document.querySelector('#form-error').textContent.length>0); assert.equal(await b.locator('[name=title]').inputValue(),'Formulario conservado'); await b.locator('#close').click(); await b.unroute('**/api/reports');
await a.goto('http://127.0.0.1:5000'); await a.locator('#theme').click(); assert.equal(await a.evaluate(()=>document.documentElement.dataset.theme),'dark'); await a.locator('#theme').click();
await a.route('**/api/reports', route => route.fulfill({json:{server_time:Date.now()/1000,reports:[{id:999,title:'QA expiración simulada',description:'Solo simulación de navegador',animal_type:'dog',status_type:'seen',latitude:-34.9,longitude:-56.1,pastel_color:'#A0C4FF',created_at:new Date().toISOString(),expires_at:new Date(Date.now()+1500).toISOString()}]}}));
await a.reload(); await a.waitForFunction(()=>document.querySelector('#reports').textContent.includes('QA expiración simulada')); await a.waitForFunction(()=>!document.querySelector('#reports').textContent.includes('QA expiración simulada'),{},{timeout:12000}); await a.unroute('**/api/reports');
await a.goto('http://127.0.0.1:5000'); await a.setViewportSize({width:1440,height:1000}); await a.waitForTimeout(2000); await a.screenshot({path:'preview-desktop.png',fullPage:true});
await a.setViewportSize({width:390,height:844}); await a.screenshot({path:'preview-mobile.png',fullPage:true});
console.log(JSON.stringify({sizes:7,sharedPublication:true,sharedDeletion:true,geolocationGranted:true,geolocationDenied:true,pageErrors:errors,tileCount:await a.locator('img.leaflet-tile-loaded').count()})); assert.equal(errors.length,0);
await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
