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
    const totalQuestions = questions.length;

    if (isNaN(targetScore) || targetScore < 0 || targetScore > 100) {
        alert("目标分数无效，必须是 0 到 100 之间的整数。");
        return;
    }

    // 计算每题分数
    const pointsPerQuestion = 100 / totalQuestions;
    console.log("每題分數：", pointsPerQuestion);

    // 计算需要答对的确切题目数量
    const targetPoints = targetScore;
    const correctQuestionsNeeded = Math.floor(targetPoints / pointsPerQuestion);
    const remainingPoints = targetPoints % pointsPerQuestion;

    console.log("需要答對題數：", correctQuestionsNeeded);
    console.log("剩餘分數：", remainingPoints);

    // 获取所有题目ID并按顺序排列
    const questionIds = questions.map(question => question.getAttribute('data-id'));
    
    // 确定哪些题目需要答对，哪些需要答错
    const correctQuestionIds = questionIds.slice(0, correctQuestionsNeeded);
    const wrongQuestionIds = questionIds.slice(correctQuestionsNeeded);

    console.log("答對題目ID：", correctQuestionIds);
    console.log("答錯題目ID：", wrongQuestionIds);

    // 遍历每个题目并填写答案
    questions.forEach(question => {
        const dataId = question.getAttribute('data-id');
        const correctAnswer = answers[dataId];

        if (correctAnswer) {
            const questionType = question.getAttribute('type');
            const shouldAnswerWrong = wrongQuestionIds.includes(dataId);

            if (questionType === '1') { // 选择题
                const inputs = Array.from(question.querySelectorAll('input[type="checkbox"], input[type="radio"]'));

                if (shouldAnswerWrong) {
                    // 答错：选择第一个错误选项
                    const wrongInputs = inputs.filter(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        return !correctAnswer.map(ans => ans.toLowerCase()).includes(optionText.toLowerCase());
                    });
                    if (wrongInputs.length > 0) {
                        // 始终选择第一个错误选项，而不是随机选择
                        wrongInputs[0].checked = true;
                    } else {
                        inputs.forEach(input => input.checked = false);
                    }
                } else {
                    // 答对：选择所有正确的选项
                    inputs.forEach(input => {
                        const optionText = input.closest('label').textContent.trim().replace(/^[A-Z]\.\s*/, '');
                        input.checked = correctAnswer.map(ans => ans.toLowerCase()).includes(optionText.toLowerCase());
                    });
                }
            } else if (questionType === '2') { // 填空题
                const inputs = question.querySelectorAll('.gap-input, input[type="text"], textarea');

                if (shouldAnswerWrong) {
                    // 答错：填入空格
                    inputs.forEach(input => {
                        input.value = " ";
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

    // 输出最终的答题统计
    const expectedScore = (correctQuestionsNeeded * pointsPerQuestion);
    console.log("預期分數：", expectedScore);
    console.log("所有答案已成功填充！");

})(arguments[0], arguments[1]);