const run = require("./browser")


async function pdf(page){
    console.error("crf表单渲染完成，开始打印。");
    var buffer = await page.pdf({
        format: process.argv[4],
        printBackground: true,
        displayHeaderFooter: true,
        headerTemplate: process.argv[8],
        footerTemplate: process.argv[9],
        margin: {
          top: "100px",
          bottom: "100px",
          right: "30px",
          left: "30px",
        }
    });
    return buffer;
}

run((async () => {}), pdf)


