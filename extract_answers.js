// 1. 选择所有 data-parentid="" 的题目元素
const questions = document.querySelectorAll('.kques-item[data-parentid=""]');

// 2. 初始化一个字符串来存储所有题目和对应的正确答案
let output = "";

// 3. 遍历每个题目元素并找到已选择的正确答案
questions.forEach((question) => {
    // 获取题目的类型属性，以区分选择题和填空题
    const questionType = question.getAttribute('type');
    
    // 获取题目的 data-id
    const dataId = question.getAttribute('data-id');

    if (questionType === '1') {  // 选择题（单选或多选）
        // 判断是多选题（checkbox）还是单选题（radio）
        const isMultipleChoice = question.querySelector('input[type="checkbox"]') !== null;
        
        // 根据类型收集已选择的选项
        const selectedOptions = isMultipleChoice
            ? Array.from(question.querySelectorAll('input[type="checkbox"][checked]'))
            : Array.from(question.querySelectorAll('input[type="radio"][checked]'));
        
        // 构建答案文本，移除前缀（例如 "A. ", "B. "）
        const answerTexts = selectedOptions
            .map(option => {
                let text = option.closest('label').textContent.trim();
                return text.replace(/^[A-Z]\.\s*/, ''); // 移除 "A.", "B." 等
            })
            .join(', ');
        output += `${dataId} - ${answerTexts || "No correct answer found"}\n`;

    } else if (questionType === '2') {  // 填空题
        // 从 gap-preview spans 中收集所有填空答案
        const blankAnswers = Array.from(question.querySelectorAll('span.gap-preview'))
            .map(blank => blank.textContent.trim())
            .join(', ');
        output += `${dataId} - ${blankAnswers || "No answers provided"}\n`;
    }
});

// 4. 一次性输出所有题目和答案
console.log(output);
return output;  // 确保输出被返回到 Selenium
