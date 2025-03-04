let currentPath = "/";
let currentPage = 1;
let uidMapping = {};
let gidMapping = {};
const perPage = 15;

$(document).ready(function () {
  loadFileList();
});

function loadSystemGroups() {
  $.get("/api/system/group/list")
    .done(function (response) {
      if (response.status === "success") {
        gidMapping = {};
        response.data.forEach(function (group) {
          gidMapping[group.gid] = group.name;
        });
      } else {
        alert("加载系统用户组信息失败");
      }
    })
    .fail(function () {
      alert("加载系统用户组信息失败");
    });
}

function loadSystemUsers() {
  $.get("/api/system/user/list")
    .done(function (response) {
      if (response.status === "success") {
        uidMapping = {};
        response.data.forEach(function (user) {
          uidMapping[user.uid] = user.name;
        });
      } else {
        alert("加载系统用户信息失败");
      }
    })
    .fail(function () {
      alert("加载系统用户信息失败");
    });
}

function loadFileList() {
  loadSystemGroups();
  loadSystemUsers();
  $.get(
    `/api/file/list?path=${encodeURIComponent(
      currentPath
    )}&page=${currentPage}&per_page=${perPage}`
  )
    .done(function (response) {
      if (response.status === "success") {
        updateFileList(response.data);
        updatePagination(response.data);
      } else {
        alert("加载文件列表失败");
      }
    })
    .fail(function () {
      alert("加载文件列表失败");
    });
}

function updateFileList(data) {
  const breadcrumb = $(".breadcrumb").empty();
  const pathArray = currentPath.split("/").filter((item) => item);
  let combinedPath = "";
  breadcrumb.append(`
        <li class="breadcrumb-item">
            <a href="javascript:void(0)" onclick="navigateTo('/')">
                <i class="fas fa-home"></i>
            </a>
        </li>
    `);
  pathArray.forEach(function (item, index) {
    combinedPath += item + "/";
    if (index === pathArray.length - 1) {
      breadcrumb.append(`
            <li class="breadcrumb-item active" aria-current="page">${item}</li>
        `);
    } else {
      breadcrumb.append(`
            <li class="breadcrumb-item">
                <a href="javascript:void(0)" onclick="navigateTo('${combinedPath}')">${item}</a>
            </li>
        `);
    }
  });
  const tbody = $("tbody").empty();
  if (currentPath !== "/") {
    const parentPath = currentPath.split("/").slice(0, -2).join("/") + "/";
    tbody.append(`
            <tr>
                <td colspan="6">
                    <a href="javascript:void(0)" onclick="navigateTo('${parentPath}')">
                        <i class="fas fa-level-up-alt"></i> 返回上级目录
                    </a>
                </td>
            </tr>
        `);
  }
  data.items.forEach(function (item) {
    const icon =
      item.type === "dir"
        ? '<i class="fas fa-folder text-warning"></i>'
        : '<i class="fas fa-file text-primary"></i>';
    const size = formatFileSize(item.size);
    const lastModified = new Date(item.last_modified * 1000).toLocaleString();
    const owner =
      (gidMapping[item.gid] || item.gid) +
      `<span class="text-secondary text-sm">（用户组）</span>` +
      (uidMapping[item.uid] || item.uid) +
      `<span class="text-secondary text-sm">（用户）</span>`;
    const actions = `
            <div class="btn-group">
                ${
                  item.type === "file"
                    ? `<button class="btn btn-sm btn-info" onclick="downloadFile('${item.name}')">
                        <i class="fas fa-download"></i>
                    </button>`
                    : ""
                }
                <button class="btn btn-sm btn-warning" onclick="showPermissionDialog('${
                  item.name
                }', ${item.uid}, ${item.gid})">
                    <i class="fas fa-key"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteFile('${
                  item.name
                }')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
    tbody.append(`
            <tr>
                <td>
                    ${icon}
                    ${
                      item.type === "dir"
                        ? `<a href="javascript:void(0)" onclick="navigateTo('${currentPath}${item.name}/')">${item.name}</a>`
                        : item.name
                    }
                    ${
                      item.target
                        ? `<span class="text-secondary text-sm">→ ${item.target}</span>`
                        : ""
                    }
                </td>
                <td>${size}</td>
                <td>${lastModified}</td>
                <td>${item.permission}</td>
                <td>${owner}</td>
                <td>${actions}</td>
            </tr>
    `);
  });
}

function updatePagination(data) {
  const footer = $(".card-footer").empty();
  const totalPages =
    Math.ceil(data.total / data.per_page) == 0
      ? 1
      : Math.ceil(data.total / data.per_page);
  const pagination = $('<ul class="pagination m-0 float-right">');
  pagination.append(`
      <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
        <a class="page-link" href="javascript:void(0)" onclick="changePage(${
          currentPage - 1
        })">上一页</a>
      </li>
    `);
  const showPages = [];
  const maxVisiblePages = 7;
  const sidePages = 2;
  showPages.push(1);
  if (totalPages <= maxVisiblePages) {
    for (let i = 2; i <= totalPages; i++) {
      showPages.push(i);
    }
  } else {
    if (currentPage <= sidePages + 3) {
      for (let i = 2; i <= sidePages + 3; i++) {
        showPages.push(i);
      }
      showPages.push("...");
      showPages.push(totalPages);
    } else if (currentPage >= totalPages - (sidePages + 2)) {
      showPages.push("...");
      for (let i = totalPages - (sidePages + 2); i <= totalPages - 1; i++) {
        showPages.push(i);
      }
      showPages.push(totalPages);
    } else {
      showPages.push("...");
      for (let i = currentPage - sidePages; i <= currentPage + sidePages; i++) {
        showPages.push(i);
      }
      showPages.push("...");
      showPages.push(totalPages);
    }
  }
  showPages.forEach((page) => {
    if (page === "...") {
      pagination.append(`
          <li class="page-item disabled">
            <span class="page-link">...</span>
          </li>
        `);
    } else {
      pagination.append(`
          <li class="page-item ${currentPage === page ? "active" : ""}">
            <a class="page-link" href="javascript:void(0)" onclick="changePage(${page})">${page}</a>
          </li>
        `);
    }
  });
  pagination.append(`
      <li class="page-item ${currentPage === totalPages ? "disabled" : ""}">
        <a class="page-link" href="javascript:void(0)" onclick="changePage(${
          currentPage + 1
        })">下一页</a>
      </li>
    `);
  footer.append(pagination);
}

function changePage(page) {
  if (page < 1) return;
  currentPage = page;
  loadFileList();
}

function navigateTo(path) {
  currentPath = path;
  currentPage = 1;
  loadFileList();
}

function formatFileSize(bytes) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function uploadFile() {
  const input = $('<input type="file" multiple style="display: none">');
  input.on("change", function (e) {
    const files = e.target.files;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    $.ajax({
      url: `/api/file/upload?path=${encodeURIComponent(currentPath)}`,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function (response) {
        if (response.status === "success") {
          loadFileList();
        } else {
          alert("上传失败：" + response.message);
        }
      },
      error: function () {
        alert("上传失败");
      },
    });
  });
  input.click();
}

function createFolder() {
  const folderName = prompt("请输入文件夹名称：");
  if (!folderName) return;
  $.post(
    `/api/file/create?path=${encodeURIComponent(
      currentPath + folderName
    )}&type=dir`
  )
    .done(function (response) {
      if (response.status === "success") {
        loadFileList();
      } else {
        alert("创建文件夹失败：" + response.message);
      }
    })
    .fail(function () {
      alert("创建文件夹失败");
    });
}

function createFile() {
  const fileName = prompt("请输入文件名：");
  if (!fileName) return;
  $.post(
    `/api/file/create?path=${encodeURIComponent(
      currentPath + fileName
    )}&type=file`
  )
    .done(function (response) {
      if (response.status === "success") {
        loadFileList();
      } else {
        alert("创建文件失败：" + response.message);
      }
    })
    .fail(function () {
      alert("创建文件失败");
    });
}

function downloadFile(fileName) {
  window.location.href = `/api/file/download?path=${encodeURIComponent(
    currentPath + fileName
  )}`;
}

function deleteFile(fileName) {
  if (!confirm("确定要删除该文件/文件夹吗？")) return;
  $.ajax({
    url: "/api/file/delete",
    type: "DELETE",
    data: { path: currentPath + fileName },
    success: function (response) {
      if (response.status === "success") {
        loadFileList();
      } else {
        alert("删除失败：" + response.message);
      }
    },
    error: function () {
      alert("删除失败");
    },
  });
}

function showPermissionDialog(fileName, currentUid, currentGid) {
  $.when($.get("/api/system/user/list"), $.get("/api/system/group/list")).done(
    function (userResponse, groupResponse) {
      if (
        userResponse[0].status === "success" &&
        groupResponse[0].status === "success"
      ) {
        const users = userResponse[0].data;
        const groups = groupResponse[0].data;
        const dialog = $(`
                <div class="modal fade" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">修改权限 - ${fileName}</h5>
                                <button type="button" class="close" data-dismiss="modal">
                                    <span>&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                <div class="form-group">
                                    <label>所有者</label>
                                    <select class="form-control" id="owner">
                                        ${users
                                          .map(
                                            (user) =>
                                              `<option value="${user.uid}" ${
                                                user.uid === currentUid
                                                  ? "selected"
                                                  : ""
                                              }>
                                                ${user.name}
                                            </option>`
                                          )
                                          .join("")}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>用户组</label>
                                    <select class="form-control" id="group">
                                        ${groups
                                          .map(
                                            (group) =>
                                              `<option value="${group.gid}" ${
                                                group.gid === currentGid
                                                  ? "selected"
                                                  : ""
                                              }>
                                                ${group.name}
                                            </option>`
                                          )
                                          .join("")}
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label>权限</label>
                                    <input type="text" class="form-control" id="mode" value="644" 
                                           placeholder="请输入权限值（如：644）">
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-primary" onclick="changePermission('${fileName}')">
                                    确定
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `);
        dialog.modal("show");
      } else {
        alert("获取用户和组信息失败");
      }
    }
  );
}

function changePermission(fileName) {
  const mode = parseInt($("#mode").val(), 8);
  const owner = parseInt($("#owner").val());
  const group = parseInt($("#group").val());
  $.ajax({
    url: "/api/file/permission",
    type: "PATCH",
    data: {
      path: currentPath + fileName,
      mode: mode,
      owner: owner,
      group: group,
    },
    success: function (response) {
      if (response.status === "success") {
        $(".modal").modal("hide");
        loadFileList();
      } else {
        alert("修改权限失败：" + response.message);
      }
    },
    error: function () {
      alert("修改权限失败");
    },
  });
}
