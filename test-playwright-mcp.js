const { chromium } = require('playwright');

async function testPlaywrightMCP() {
  console.log('Playwright MCPサーバーのテストを開始します...');
  
  try {
    // ブラウザを起動
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    // テスト用のページにアクセス
    await page.goto('https://example.com');
    
    // ページタイトルを取得
    const title = await page.title();
    console.log('ページタイトル:', title);
    
    // スクリーンショットを撮影
    await page.screenshot({ path: 'test-screenshot.png' });
    console.log('スクリーンショットを保存しました: test-screenshot.png');
    
    // ブラウザを閉じる
    await browser.close();
    
    console.log('テストが正常に完了しました！');
  } catch (error) {
    console.error('エラーが発生しました:', error);
  }
}

testPlaywrightMCP(); 