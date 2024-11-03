// 移除所有難易度顯示
function removePropertyElements() {
    const propertyElements = document.querySelectorAll('.property');
    propertyElements.forEach(element => element.remove());
}

// 為 type="1"（選擇題）和 type="2"（填充題）的題目添加書籤圖標
const questions = document.querySelectorAll('.kques-item[type="1"], .kques-item[type="2"]');
questions.forEach(question => {
    // 檢查是否已經有書籤圖標，避免重複插入
    if (!question.querySelector('.glyphicon-bookmark')) {
        question.insertAdjacentHTML('beforeend', '<i class="glyphicon glyphicon-bookmark bookmark kexamFocus"></i>');
    }
});

// 刪除所有 .explaination 元素
document.querySelectorAll('.explaination').forEach(explaination => {
    explaination.remove();
});

console.log('所有 .explaination 元素已被刪除');

// 預設倒數時間（以分鐘計）
// 將此設置為 0 或者其他正整數以進行預設
let countdownTime = 10; // 預設為 0，表示需要用戶輸入時間

// 如果預設的時間為 0 或無效，則提示用戶輸入
if (isNaN(countdownTime) || countdownTime <= 0) {
    countdownTime = parseInt(prompt("請輸入要倒數的時間（分鐘）："), 10);
}

// 檢查輸入是否為有效的數字
if (!isNaN(countdownTime) && countdownTime > 0) {
    countdownTime *= 60; // 將分鐘轉換為秒數

    // 定義倒數計時功能
    function startCountdown() {
        const timerElement = document.querySelector('.tool-timer .timer');
    
        if (timerElement) {
            const interval = setInterval(() => {
                if (countdownTime > 0) {
                    const hours = Math.floor(countdownTime / 3600);
                    const minutes = Math.floor((countdownTime % 3600) / 60);
                    const seconds = countdownTime % 60;
    
                    timerElement.textContent = 
                        `${hours.toString().padStart(2, '0')}:` +
                        `${minutes.toString().padStart(2, '0')}:` +
                        `${seconds.toString().padStart(2, '0')}`;
    
                    console.log(`更新時間: ${timerElement.textContent}`); // 確認是否正在更新
                    countdownTime--;
                } else {
                    clearInterval(interval);
                    timerElement.textContent = '時間到！';
                    alert('時間到！');
                }
            }, 1000);
        } else {
            console.error("找不到 .tool-timer .timer 元素，請確認 DOM 結構是否正確。");
        }
    }
    

    // 等待 DOM 加載完成後執行
    document.addEventListener("DOMContentLoaded", () => {
        startCountdown();
    });
} else {
    alert("請輸入有效的時間（正整數）。");
}

// 創建工具欄
function createFixedToolbar() {
    // 移除現有的 toolbar（如果存在）
    const existingToolbar = document.querySelector('.toolbar.fix-to-top.container');
    if (existingToolbar) {
        existingToolbar.remove();
    }

    // 找到正確的插入位置
    const kexamTake = document.querySelector('#kexam-take');
    if (!kexamTake) return;

    // 確保有一個空白的 div 用於間距
    const blank = document.createElement('div');
    blank.className = 'blank';
    blank.style.height = '37.9948px';

    // 獲取題目信息，計算所有選擇題和填充題的總數
    const questions = Array.from(document.querySelectorAll('.kques-item'));
    const questionCount = document.querySelectorAll('.kques-item[type="1"], .kques-item[type="2"]').length;

    // 創建 toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'toolbar clearfix';
    toolbar.innerHTML = `
        <div class="tool-doneQues">
            <div class="sn-list">
                <div class="dropdown pull-right" style="">
                    <a class="dropdown-toggle" data-toggle="dropdown">已作答: 
                        <span class="done-cnt">0</span> /
                        <span class="total-num">${questionCount}</span> 題<span class="caret"></span>
                    </a>
                    <ul class="dropdown-menu" style="">
                        ${questions.map((item, index) => {
                            const id = item.getAttribute('data-id');
                            const sn = item.querySelector('.sn')?.textContent || '說明';
                            return `<li><a class="sn-list-opt sn" data-id="${id}" data-sn="${index + 1}" state="">${sn}</a></li>`;
                        }).join('')}
                    </ul>
                </div>
            </div>
        </div>
        <div class="tool-name">
            姓名: xxx,
        </div>
        <div class="tool-pass">
            測驗及格: 60分
        </div>
        <div class="tool-submit">
            <button type="button" class="btn btn-primary" role="submit-exam">交卷</button>
        </div>
        <div class="tool-timer hidden">
            <i class="glyphicon glyphicon-time"></i> <span class="timer">00:00:00</span>
        </div>
    `;

    // 使用正確的插入順序
    kexamTake.insertBefore(blank, kexamTake.firstChild);
    kexamTake.insertBefore(toolbar, blank.nextSibling);

    // 添加下拉菜單功能
    document.addEventListener('click', function (e) {
        const dropdownToggle = e.target.closest('.dropdown-toggle');
        const isDropdownClick = e.target.closest('.dropdown-menu');

        if (dropdownToggle) {
            dropdownToggle.closest('.dropdown').classList.toggle('open');
            e.preventDefault();
            e.stopPropagation();
        } else if (!isDropdownClick) {
            document.querySelectorAll('.dropdown').forEach(dropdown => {
                dropdown.classList.remove('open');
            });
        }
    });

    // 添加題目快速跳轉功能
    toolbar.querySelectorAll('.sn-list-opt').forEach(opt => {
        opt.addEventListener('click', function (e) {
            const targetId = this.getAttribute('data-id');
            const targetElement = document.querySelector(`[data-id="${targetId}"]`);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            e.preventDefault();
        });
    });
}

// 創建自定義對話框
function createCustomModal(message) {
    const modalHTML = `
        <div class="modal fade" id="customSubmitModal" tabindex="-1" role="dialog" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-body">
                        <button type="button" class="bootbox-close-button close" data-dismiss="modal" aria-hidden="true" style="margin-top: -10px;">×</button>
                        <div class="bootbox-body">${message}</div>
                    </div>
                    <div class="modal-footer">
                        <button data-bb-handler="cancel" type="button" class="btn btn-default">取消</button>
                        <button data-bb-handler="confirm" type="button" class="btn btn-primary">交卷</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 移除舊的 modal（如果存在）
    const oldModal = document.getElementById('customSubmitModal');
    if (oldModal) {
        oldModal.remove();
    }

    // 添加新的 modal
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    return document.getElementById('customSubmitModal');
}

// 顯示自定義對話框
function showCustomConfirm(message, callback) {
    const modal = createCustomModal(message);
    const $modal = $(modal);

    // 綁定按鈕事件
    modal.querySelector('[data-bb-handler="confirm"]').addEventListener('click', function() {
        $modal.modal('hide');
        callback(true);
    });

    modal.querySelector('[data-bb-handler="cancel"]').addEventListener('click', function() {
        $modal.modal('hide');
        callback(false);
    });

    modal.querySelector('.bootbox-close-button').addEventListener('click', function() {
        $modal.modal('hide');
        callback(false);
    });

    // 顯示對話框
    $modal.modal('show');
}

// 啟用所有的選擇題與填充題編輯功能，並調整樣式以匹配原始設計
function enableExamFunction() {
    const questions = document.querySelectorAll('.kques-item');

    questions.forEach(question => {
        const questionType = question.getAttribute('type');

        if (questionType === '1') {
            // 選擇題：啟用所有選項
            const options = question.querySelectorAll('input[type="radio"], input[type="checkbox"]');
            options.forEach(option => {
                option.removeAttribute('disabled');
            });
        } else if (questionType === '2') {
            // 填充題：啟用所有輸入框和文本框，包括嵌套在特定標籤中的元素
            const inputFields = question.querySelectorAll('input[type="text"], textarea');
            inputFields.forEach(input => {
                input.removeAttribute('disabled');
                input.removeAttribute('readonly');
                input.style.pointerEvents = 'auto'; // 確保可以點擊編輯
                input.classList.add('gap-input'); // 添加 class 以匹配樣式
                input.size = 10; // 設定大小，根據需要調整
            });

            // 確保內嵌的 div/span 等標籤沒有阻止編輯，並替換為具有自訂樣式的輸入框
            const editableSpans = question.querySelectorAll('span.gap-preview, div.gap-preview');
            editableSpans.forEach(span => {
                const input = document.createElement('input');
                input.type = 'text';
                input.value = span.textContent.trim();
                input.classList.add('gap-input'); // 添加 class 以匹配樣式
                input.size = 10; // 設定大小
                input.style.pointerEvents = 'auto';
                input.style.backgroundColor = 'transparent'; // 背景透明
                input.style.border = 'none'; // 無邊框
                input.style.borderBottom = '1px solid #000'; // 添加底線
                
                // 替換 span 為輸入框
                span.replaceWith(input);
            });
        }
    });

    console.log('所有題目已設置為可編輯，並應保持樣式一致');
}

// 在初始化中調用 enableExamFunction 來確保頁面加載後所有題目都是可編輯的
document.addEventListener("DOMContentLoaded", () => {
    enableExamFunction();
});

// 更新已作答數量顯示
function updateAnsweredCount() {
    const questions = document.querySelectorAll('.kques-item');
    let answeredCount = 0;

    questions.forEach(question => {
        const questionType = question.getAttribute('type');
        if (questionType === '1') {
            // 計算選擇題是否已作答
            const checkedOption = question.querySelector('input:checked');
            if (checkedOption) {
                answeredCount++;
            }
        } else if (questionType === '2') {
            // 計算填充題是否已作答
            const inputFields = question.querySelectorAll('input[type="text"], textarea');
            let filled = true;
            inputFields.forEach(input => {
                if (input.value.trim() === '') {
                    filled = false;
                }
            });
            if (filled) {
                answeredCount++;
            }
        }
    });

    // 更新已作答的題目數量
    document.querySelector('.done-cnt').textContent = answeredCount;
}

// 檢查是否有未回答的題目
function checkUnansweredQuestions() {
    const questions = document.querySelectorAll('.kques-item[type="1"]');
    let hasUnanswered = false;
    
    questions.forEach(question => {
        const checkedOption = question.querySelector('input:checked');
        if (!checkedOption) {
            hasUnanswered = true;
        }
    });
    
    return hasUnanswered;
}

// 收集答案，包括填充題的答案
function collectAnswers() {
    const answers = {};
    const questions = document.querySelectorAll('.kques-item');

    questions.forEach(question => {
        const questionId = question.getAttribute('data-id');
        const questionType = question.getAttribute('type');

        if (questionType === '1') {
            const selectedOption = question.querySelector('input:checked');
            if (selectedOption) {
                answers[questionId] = selectedOption.value;
            }
        } else if (questionType === '2') {
            const inputFields = question.querySelectorAll('input[type="text"], textarea');
            const inputsArray = Array.from(inputFields).map(input => input.value.trim());
            if (inputsArray.length > 0 && inputsArray.some(val => val !== '')) {
                answers[questionId] = inputsArray;
            }
        }
    });

    return answers;
}

// 關閉頁面函數
function closePage() {
    // 嘗試使用不同的方法關閉頁面
    window.close();
    
    // 如果 window.close() 不起作用，嘗試返回上一頁
    if (document.referrer) {
        window.location.href = document.referrer;
    } else {
        window.location.href = "/course/exam/26696";
    }
}

// 處理提交
function handleFormSubmit() {
    document.querySelectorAll('button[role="submit-exam"]').forEach(button => {
        button.removeEventListener('click', handleSubmitClick);
        button.addEventListener('click', handleSubmitClick);
    });
}

// 提交點擊處理函數
function handleSubmitClick(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const hasUnanswered = checkUnansweredQuestions();
    const confirmMessage = hasUnanswered ? 
        "尚有未作答的題目，確定要交卷?" : 
        "確定要交卷?";

    showCustomConfirm(confirmMessage, function(result) {
        if (result) {
            const answers = collectAnswers();
            console.log('提交的答案：', answers);
            
            // 防止任何確認對話框
            window.onbeforeunload = null;
            
            // 禁用所有表單提交事件
            document.querySelectorAll('form').forEach(form => {
                form.onsubmit = (e) => {
                    e.preventDefault();
                    return false;
                };
            });
            
            // 關閉頁面
            closePage();
        }
    });
}

// 防止預覽模式提示
function preventPreviewMode() {
    if (window.fs && window.fs.kexamTake) {
        window.fs.kexamTake.isPreview = function() { return false; };
    }
    document.removeEventListener('fs.kexam.preview', function(){}, true);
}

// 初始化整個考試系統
function initializeExamSystem() {
    removePropertyElements();
    createFixedToolbar();
    enableExamFunction();
    preventPreviewMode();
    handleFormSubmit();

    // 添加必要的 CSS 樣式
    const modalStyle = document.createElement('style');
    modalStyle.textContent = `
        .modal-backdrop.fade.in {
            opacity: 0.5;
        }
        #customSubmitModal .modal-dialog {
            margin: 30px auto;
        }
        #customSubmitModal .modal-content {
            border-radius: 6px;
        }
        #customSubmitModal .modal-body {
            padding: 20px;
            position: relative;
        }
        #customSubmitModal .modal-footer {
            padding: 15px;
            text-align: right;
            border-top: 1px solid #e5e5e5;
        }
        #customSubmitModal .bootbox-body {
            padding-right: 15px;
        }
    `;
    document.head.appendChild(modalStyle);
}

// 執行初始化
initializeExamSystem();
console.log('考試系統已完整啟用');