(function() {
    // 1. 原始答案字串，使用 data-id 作為鍵
    const answerInput = `

`;

    // 2. 解析答案字串並轉換為對象格式
    const answers = {};
    answerInput.trim().split('\n').forEach(line => {
        const [id, answerPart] = line.split(' - ');
        if (id && answerPart) {
            const answerValues = answerPart.split(',').map(ans => ans.trim());
            answers[id.trim()] = answerValues;
        }
    });

    // 3. 獲取所有題目元素
    const questions = document.querySelectorAll('.kques-item[data-parentid=""]');

    // 4. 遍歷每個題目並填寫答案
    questions.forEach(question => {
        const dataId = question.getAttribute('data-id');
        const answer = answers[dataId];

        if (answer) {
            const questionType = question.getAttribute('type');

            if (questionType === '1') { // 選擇題
                // 獲取所有選項的 input 元素
                const inputs = question.querySelectorAll('input[type="checkbox"], input[type="radio"]');
                
                // 對每個答案進行處理
                answer.forEach(ans => {
                    inputs.forEach(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        if (optionText.trim() === ans.trim()) {
                            input.checked = true;
                        }                        
                    });
                });

            } else if (questionType === '2') { // 填空題
                // 獲取所有填空的 input 元素（包括 .gap-input 類和 type="text" 的 input）
                const inputs = question.querySelectorAll('.gap-input, input[type="text"]');

                // 將答案填入輸入框
                answer.forEach((ans, idx) => {
                    if (inputs[idx]) {
                        inputs[idx].value = ans;
                    }
                });
            }
        }
    });

    console.log("所有答案已成功填充！");
})();
