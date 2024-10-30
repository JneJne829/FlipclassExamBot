(function(answerInput, targetScore) {
    // 1. 原始答案字符串，使用 data-id 作为键
    console.log("接收到的答案字符串：", answerInput);
    console.log("目标分数：", targetScore);

    // 3. 解析答案字符串并转换为对象格式
    const answers = {};
    answerInput.trim().split('\n').forEach(line => {
        const [id, answerPart] = line.split(' - ');
        if (id && answerPart) {
            const answerValues = answerPart.split(',').map(ans => ans.trim());
            answers[id.trim()] = answerValues;
        }
    });

    console.log("解析后的答案对象：", answers);
    
    // 4. 获取所有题目元素
    const questions = Array.from(document.querySelectorAll('.kques-item[data-parentid=""]'));

    // 5. 计算需要答错的题目数量
    const totalQuestions = questions.length;

    if (isNaN(targetScore) || targetScore < 0 || targetScore > 100) {
        alert("目标分数无效，必须是 0 到 100 之间的整数。");
        return;
    }

    // **使用 Math.ceil() 确保答对的题目数足以达到目标分数**
    const correctQuestionsNeeded = Math.ceil((targetScore / 100) * totalQuestions);
    const wrongQuestionsNeeded = totalQuestions - correctQuestionsNeeded;

    console.log(`总题数: ${totalQuestions}, 需要答对: ${correctQuestionsNeeded}, 需要答错: ${wrongQuestionsNeeded}`);

    // 6. 随机选择需要答错的题目
    const questionIds = questions.map(question => question.getAttribute('data-id'));
    const wrongQuestionIds = [];

    if (wrongQuestionsNeeded > 0) {
        while (wrongQuestionIds.length < wrongQuestionsNeeded) {
            const randomId = questionIds[Math.floor(Math.random() * questionIds.length)];
            if (!wrongQuestionIds.includes(randomId)) {
                wrongQuestionIds.push(randomId);
            }
        }
    }

    // 7. 遍历每个题目并填写答案
    questions.forEach(question => {
        const dataId = question.getAttribute('data-id');
        const correctAnswer = answers[dataId];

        if (correctAnswer) {
            const questionType = question.getAttribute('type');

            // 检查该题是否需要答错
            const shouldAnswerWrong = wrongQuestionIds.includes(dataId);

            if (questionType === '1') { // 选择题
                // 获取所有选项的 input 元素
                const inputs = Array.from(question.querySelectorAll('input[type="checkbox"], input[type="radio"]'));

                if (shouldAnswerWrong) {
                    // 答错：选择一个错误的选项
                    const wrongInputs = inputs.filter(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        return !correctAnswer.map(ans => ans.toLowerCase()).includes(optionText.toLowerCase());
                    });
                    if (wrongInputs.length > 0) {
                        // 随机选择一个错误选项
                        const randomWrongInput = wrongInputs[Math.floor(Math.random() * wrongInputs.length)];
                        randomWrongInput.checked = true;
                    } else {
                        // 如果没有错误选项，则不选择任何选项
                        inputs.forEach(input => input.checked = false);
                    }
                } else {
                    // 答对：选择正确的选项
                    inputs.forEach(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        if (correctAnswer.map(ans => ans.toLowerCase()).includes(optionText.toLowerCase())) {
                            input.checked = true;
                        }
                    });
                }
            } else if (questionType === '2') { // 填空题
                // 获取所有填空的 input 元素
                const inputs = question.querySelectorAll('.gap-input, input[type="text"], textarea');

                if (shouldAnswerWrong) {
                    // 答错：填入一个错误答案
                    inputs.forEach(input => {
                        input.value = " "; // 您可以自定义错误答案
                    });
                } else {
                    // 答对：填入正确答案
                    correctAnswer.forEach((ans, idx) => {
                        if (inputs[idx]) {
                            inputs[idx].value = ans;
                        }
                    });
                }
            }
        }
    });

    console.log("所有答案已成功填充！");

})(arguments[0], arguments[1]);
