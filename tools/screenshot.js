const run = require("./browser")

const clip = JSON.parse(process.argv[8]);

async function pic(page){
     console.error("渲染完成，开始截图。");
     return await page.screenshot({"clip": clip, "format": process.argv[4]
     });
}

async function init(page){
     console.error("调整浏览器窗口大小。");
     await page.setViewport({"width": clip["width"], "height": clip["height"]})
}

run(init, pic)

