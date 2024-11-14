// 1. 選擇所有題目元素
const questions = document.querySelectorAll('.kques-item');

// 2. 初始化一個字符串來存储所有題目和對應的正確答案
let output = "";

// 3. 遍歷每個題目元素並找到已選擇的正確答案
questions.forEach((question) => {
    // 獲取題目的類型屬性，以區分選擇題和填空題 
    const questionType = question.getAttribute('type');
    
    // 獲取題目的 data-id
    const dataId = question.getAttribute('data-id');

    if (questionType === '0') {  // 是非題
        const selectedOption = question.querySelector('input[type="radio"][checked]');
        if (selectedOption) {
            const answerText = selectedOption.closest('label').querySelector('.option').textContent.trim();
            output += `${dataId} - ${answerText}\n`;
        } else {
            output += `${dataId} - 未作答\n`;
        }
    } else if (questionType === '1') {  // 選擇題（單選或多選）
        // 判斷是多選題（checkbox）還是單選題（radio）
        const isMultipleChoice = question.querySelector('input[type="checkbox"]') !== null;
        
        // 根據類型收集已選擇的選項
        const selectedOptions = isMultipleChoice
            ? Array.from(question.querySelectorAll('input[type="checkbox"][checked]'))
            : Array.from(question.querySelectorAll('input[type="radio"][checked]'));
        
        // 構建答案文本，移除前綴（例如 "A. ", "B. "）
        const answerTexts = selectedOptions
            .map(option => {
                let text = option.closest('label').textContent.trim();
                return text.replace(/^[A-Z]\.\s*/, ''); // 移除 "A.", "B." 等
            })
            .join('、');
        output += `${dataId} - ${answerTexts || "未作答"}\n`;

    } else if (questionType === '2') {  // 填空題
        // 從 gap-preview spans 中收集所有填空答案
        const blankAnswers = Array.from(question.querySelectorAll('span.gap-preview'))
            .map(blank => blank.textContent.trim())
            .join('、');
        output += `${dataId} - ${blankAnswers || "未作答"}\n`;
    }
});

// 4. 一次性輸出所有題目和答案
console.log(output);
return output;  // 確保輸出被返回到 Selenium