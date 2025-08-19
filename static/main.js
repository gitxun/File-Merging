const socket = io();

let selectedWordFiles = [];
let currentModuleConfig = null; // 当前已加载/编辑的模块配置
let useEditedModuleConfig = false; // 是否优先使用编辑过的配置
let currentModuleConfigFileName = null; // 新增：当前配置文件名


// 点击卡片触发input
function triggerInput(inputId) {
    document.getElementById(inputId).click();
}

// 选择Word文件
document.getElementById('input_files_picker').addEventListener('change', function () {
    selectedWordFiles = Array.from(this.files);
    updateWordFileList();
    updateWordCardStatus();
});

// 选择模块配置文件
document.getElementById('module_config_picker').addEventListener('change', function () {
    showModuleConfigPreview();
    updateModuleCardStatus();

    // 选择新文件时取消“使用编辑内容”状态
    useEditedModuleConfig = false;
    document.getElementById("edit_status_hint").style.display = "none";

    const files = this.files;
    if (files.length > 0) {
        const f = files[0];
        currentModuleConfigFileName = f.name;  // 记录文件名
        const reader = new FileReader();
        reader.onload = function (e) {
            try {
                currentModuleConfig = JSON.parse(e.target.result);
                if (!Array.isArray(currentModuleConfig.module_titles)) {
                    currentModuleConfig.module_titles = [];
                }
                renderModuleTitlesEditor();
                document.getElementById('module_titles_editor').style.display = 'block';
            } catch (err) {
                alert('模块配置文件格式不正确！');
                currentModuleConfig = { module_titles: [] };
                renderModuleTitlesEditor();
                document.getElementById('module_titles_editor').style.display = 'block';
            }
        };
        reader.readAsText(f);
    } else {
        // 文件清空时，隐藏编辑区并清空文件名变量
        document.getElementById('module_titles_editor').style.display = 'none';
        currentModuleConfig = null;
        currentModuleConfigFileName = null;
        renderModuleTitlesEditor();
    }
});


function renderModuleTitlesEditor() {
    const list = document.getElementById('module_titles_list');
    list.innerHTML = '';
    if (!currentModuleConfig || !Array.isArray(currentModuleConfig.module_titles)) return;
    currentModuleConfig.module_titles.forEach((title, idx) => {
        const li = document.createElement('li');
        li.style.marginBottom = '6px';
        // 可编辑输入框
        const input = document.createElement('input');
        input.type = 'text';
        input.value = title;
        input.style.width = '220px';
        input.onchange = function () { editModuleTitle(idx, this.value); };
        // 删除按钮
        const del = document.createElement('button');
        del.innerText = '删除';
        del.style.marginLeft = '8px';
        del.onclick = function () { removeModuleTitle(idx); };
        li.appendChild(input);
        li.appendChild(del);
        list.appendChild(li);
    });
}

function addModuleTitle() {
    if (currentModuleConfig && Array.isArray(currentModuleConfig.module_titles)) {
        currentModuleConfig.module_titles.push('新模块');
        renderModuleTitlesEditor();
    }
}
function removeModuleTitle(idx) {
    if (currentModuleConfig && Array.isArray(currentModuleConfig.module_titles)) {
        currentModuleConfig.module_titles.splice(idx, 1);
        renderModuleTitlesEditor();
    }
}
function editModuleTitle(idx, value) {
    if (currentModuleConfig && Array.isArray(currentModuleConfig.module_titles)) {
        currentModuleConfig.module_titles[idx] = value;
    }
}

function saveModuleConfig() {
    if (!currentModuleConfig) {
        alert('没有可以保存的模块配置！');
        return;
    }
    const dataStr = JSON.stringify(currentModuleConfig, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'module_config.json';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        URL.revokeObjectURL(a.href);
        document.body.removeChild(a);
    }, 100);
    alert('已保存，请用“选择模块配置文件”重新加载新文件即可。');
}

// 新增：应用编辑内容按钮行为
function applyEditedModuleConfig() {
    // 原来是显示绿色提示
    // document.getElementById('edit_status_hint').style.display = 'block';

    // 你要改成alert弹窗提示
    alert('当前操作将上传你编辑后的模块配置');

    // 这里可以继续你的上传逻辑，比如：
    // uploadModuleConfig();
}

// --------------------文件卡片及列表交互--------------------
function updateWordFileList() {
    const ul = document.getElementById('input_files_list');
    ul.innerHTML = '';
    selectedWordFiles.forEach((f, idx) => {
        const li = document.createElement('li');
        li.title = f.name;
        li.style.cursor = 'pointer';

        // 点击切换全部显示
        li.onclick = function (event) {
            if (event.target.closest('.remove-file')) return;
            this.classList.toggle('show-full');
        };

        const icon = document.createElement('i');
        icon.className = 'file-icon bi bi-file-earmark-word word';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'filename';
        nameSpan.textContent = f.name.length > 17
            ? f.name.slice(0, 7) + '...' + f.name.slice(-7)
            : f.name;

        const del = document.createElement('span');
        del.innerHTML = '<i class="bi bi-x-circle-fill remove-file"></i>';
        del.title = '移除此文件';
        del.onclick = function (event) {
            event.stopPropagation();
            selectedWordFiles.splice(idx, 1);
            updateWordFileList();
            updateInputFilesPicker();
            updateWordCardStatus();
        };

        li.appendChild(icon);
        li.appendChild(nameSpan);
        li.appendChild(del);
        ul.appendChild(li);
        bindPreviewHoverEffect();
    });
}

function updateInputFilesPicker() {
    const dt = new DataTransfer();
    selectedWordFiles.forEach(f => dt.items.add(f));
    document.getElementById('input_files_picker').files = dt.files;
}

function updateWordCardStatus() {
    const card = document.getElementById('input_files_card');
    const check = document.getElementById('input_files_checked');
    if (selectedWordFiles.length > 0) {
        card.classList.add('selected');
        check.classList.remove('d-none');
    } else {
        card.classList.remove('selected');
        check.classList.add('d-none');
    }
}

// 模块文件（单选）逻辑
function showModuleConfigPreview() {
    const ul = document.getElementById('module_config_list');
    ul.innerHTML = '';
    const files = document.getElementById('module_config_picker').files;
    if (files.length > 0) {
        const f = files[0];
        const li = document.createElement('li');
        li.title = f.name;
        li.style.cursor = 'pointer';

        li.onclick = function (event) {
            if (event.target.closest('.remove-file')) return;
            this.classList.toggle('show-full');
        };

        const icon = document.createElement('i');
        icon.className = 'file-icon bi bi-file-earmark-text json';

        const nameSpan = document.createElement('span');
        nameSpan.className = 'filename';
        nameSpan.textContent = f.name.length > 17
            ? f.name.slice(0, 7) + '...' + f.name.slice(-7)
            : f.name;

        const del = document.createElement('span');
        del.innerHTML = '<i class="bi bi-x-circle-fill remove-file"></i>';
        del.title = '移除此文件';
        del.onclick = function (event) {
            event.stopPropagation();
            document.getElementById('module_config_picker').value = '';
            showModuleConfigPreview();
            updateModuleCardStatus();

            // 删除配置文件时，取消“使用编辑内容”状态
            useEditedModuleConfig = false;
            document.getElementById("edit_status_hint").style.display = "none";
            // 隐藏编辑区
            document.getElementById('module_titles_editor').style.display = 'none';
            currentModuleConfigFileName = null;  // ★★★ 这里赋值
        };

        li.appendChild(icon);
        li.appendChild(nameSpan);
        li.appendChild(del);
        ul.appendChild(li);
        bindPreviewHoverEffect();
    }
}

function updateModuleCardStatus() {
    const card = document.getElementById('module_config_card');
    const check = document.getElementById('module_config_checked');
    if (document.getElementById('module_config_picker').files.length > 0) {
        card.classList.add('selected');
        check.classList.remove('d-none');
    } else {
        card.classList.remove('selected');
        check.classList.add('d-none');
    }
}

function bindPreviewHoverEffect() {
    // Word文件
    document.querySelectorAll('#input_files_list li').forEach(li => {
        li.addEventListener('mouseenter', function () {
            document.getElementById('input_files_card').classList.add('selected');
        });
        li.addEventListener('mouseleave', function () {
            if (selectedWordFiles.length === 0) {
                document.getElementById('input_files_card').classList.remove('selected');
            }
        });
    });
    // 模块文件
    document.querySelectorAll('#module_config_list li').forEach(li => {
        li.addEventListener('mouseenter', function () {
            document.getElementById('module_config_card').classList.add('selected');
        });
        li.addEventListener('mouseleave', function () {
            if (document.getElementById('module_config_picker').files.length === 0) {
                document.getElementById('module_config_card').classList.remove('selected');
            }
        });
    });
}

// ----------------------------
// 合并处理相关
// ----------------------------

let isProcessing = false;

function resetProcessBtn() {
    const startBtn = document.getElementById("start-process-btn");
    isProcessing = false;
    startBtn.disabled = false;
    startBtn.innerText = "开始处理";
}

function startProcess() {
    const startBtn = document.getElementById("start-process-btn");
    if (isProcessing) {
        alert("已经在处理中，请勿重复点击。");
        return;
    }
    isProcessing = true;
    startBtn.disabled = true;
    startBtn.innerText = "处理中...";

    const inputFiles = document.getElementById("input_files_picker").files;
    const moduleConfigFiles = document.getElementById("module_config_picker").files;
    const days = document.getElementById("days").value;

    if (!inputFiles.length) {
        alert("请选择要合并的Word文件！");
        resetProcessBtn();
        return;
    }
    if (!moduleConfigFiles.length) {
        alert("请选择模块配置文件！");
        resetProcessBtn();
        return;
    }

    // 初始化进度显示
    document.getElementById("processing-info").style.display = "inline-flex";
    document.getElementById("progress").style.width = "0%";
    document.getElementById("progress").innerText = "0%";
    document.getElementById("current_step").innerText = "无";
    document.getElementById("current_step_time").innerText = "00:00:00";
    document.getElementById("total_time").innerText = "00:00:00";

    const formData = new FormData();
    for (let f of inputFiles) {
        formData.append("files", f, f.name);
    }

   // ============= 关键部分 BEGIN ==============
    if (useEditedModuleConfig && currentModuleConfig && Array.isArray(currentModuleConfig.module_titles)) {
        const dataStr = JSON.stringify(currentModuleConfig, null, 2);
        // 用原文件名，保证后端能识别替换
        const fileName = currentModuleConfigFileName || "module_config.json";
        const file = new File([dataStr], fileName, { type: "application/json" });
        formData.append("module_config", file);
    } else {
        formData.append("module_config", moduleConfigFiles[0]);
    }
    // ============= 关键部分 END ==============

    formData.append("days", days);

    fetch("/start", {
        method: "POST",
        body: formData
    }).then(res => res.json()).then(data => {
        if (data.status === "error") {
            alert("❌ " + data.message);
            document.getElementById("processing-info").style.display = "none";
            resetProcessBtn();
        }
        // 正常则等socket推送
    }).catch(err => {
        alert("请求失败：" + err);
        document.getElementById("processing-info").style.display = "none";
        resetProcessBtn();
    });
}

// 处理完成后，处理下载
socket.on("process_done", data => {
    document.getElementById("processing-info").style.display = "none";
    resetProcessBtn();

    if (data.download_url) {
        const downloadBtn = document.getElementById("download-result-btn");
        downloadBtn.href = data.download_url;
        downloadBtn.classList.remove("d-none");
        alert("处理完成！请点击“下载结果文件”获取处理后的文档。");
    } else {
        alert("处理完成，但未生成可下载结果。");
    }
});

// 进度更新
socket.on("progress_update", data => {
    if (typeof data.percent === "number" && !isNaN(data.percent)) {
        document.getElementById("progress").style.width = data.percent + "%";
        document.getElementById("progress").textContent = data.percent.toFixed(1) + "%";
    } else {
        document.getElementById("progress").style.width = "100%";
        document.getElementById("progress").textContent = "";
    }
    document.getElementById("current_step").textContent = data.current_step_name || "无";
    document.getElementById("current_step_time").textContent = data.current_step_elapsed || "00:00:00";
    document.getElementById("total_time").textContent = data.total_elapsed || "00:00:00";

    const historyList = document.getElementById("history");
    historyList.innerHTML = "";
    (data.history || []).forEach((h, idx) => {
        const li = document.createElement("li");
        li.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");
        li.innerHTML = `<span><i class="bi bi-check-circle text-success"></i> ${h.name}</span><span class="badge bg-light text-secondary">${h.time}</span>`;
        historyList.appendChild(li);
    });

    if (data.status && data.status === "done") {
        document.getElementById("processing-info").style.display = "none";
        resetProcessBtn();
    }
    if (data.status && data.status === "error") {
        document.getElementById("processing-info").style.display = "none";
        alert("处理出现错误：" + (data.message || "未知错误"));
        resetProcessBtn();
    }
});
