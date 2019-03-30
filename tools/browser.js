const puppeteer = require('puppeteer');

const cookies = JSON.parse(process.argv[2]);


async function run(init, print){
    const browser = await puppeteer.launch({args: ['--no-sandbox', '--disable-setuid-sandbox']});
    try{
        console.error("浏览器已打开。");
        const page = await browser.newPage();
        page.on('response', response => console.error(`url: ${response.url().indexOf("data:application") == -1 ? response.url() : "nouse"}, status: ${response.status()}`));
        page.on('error', error => console.error(error.stack));
        page.on('console', console.error);
        console.error("初始化");
        await init(page);
        console.error("跳转到who", process.argv[6]);
        await page.goto(process.argv[6]);
        var text = await page.content();
        console.error("who接口返回以下信息：", text);
        console.error("加入cookie。")
        var result = await page.setCookie(...cookies);
        console.error("cookie加入结果：", result);
        console.error("加入localStorage。");
        await page.evaluate(x => {
            //console.log("传入的localStorage", x);
            localStorage['sd.profile'] = x;
            //console.log("打印localStorage", localStorage.getItem("sd.profile"));
          }, process.argv[5]);

        console.error("再次跳转到", process.argv[3]);
        await page.goto(process.argv[3]);
        console.error("等待crf表单渲染完成。")
        await page.waitForSelector(process.argv[7]);
        var buffer = await print(page);
        console.error("将buffer写入标准输出。");
        await process.stdout.write(buffer);
    } finally{
        await browser.close();
    }
}

module.exports = run;