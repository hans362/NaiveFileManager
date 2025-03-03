let currentPath = "/";
let currentPage = 1;
const perPage = 10;

$(document).ready(function () {
  loadFileList();
});

function loadFileList() {
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
  const tbody = $("tbody").empty();

  // 添加返回上级目录的行（如果不在根目录）
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

  // 添加文件和目录
  data.items.forEach(function (item) {
    const icon =
      item.type === "dir"
        ? '<i class="fas fa-folder text-warning"></i>'
        : '<i class="fas fa-file text-primary"></i>';

    const size = item.type === "dir" ? "-" : formatFileSize(item.size);
    const lastModified = new Date(item.last_modified * 1000).toLocaleString();

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
                </td>
                <td>${size}</td>
                <td>${lastModified}</td>
                <td>${item.uid}</td>
                <td>${item.gid}</td>
                <td>${actions}</td>
            </tr>
        `);
  });
}

function updatePagination(data) {
  const footer = $(".card-footer").empty();
  const totalPages = Math.ceil(data.total / data.per_page);

  if (totalPages > 1) {
    const pagination = $('<ul class="pagination pagination-sm m-0 float-right">');
    
    // 上一页按钮
    pagination.append(`
      <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
        <a class="page-link" href="javascript:void(0)" onclick="changePage(${currentPage - 1})">上一页</a>
      </li>
    `);

    // 智能分页逻辑
    const showPages = [];
    const maxVisiblePages = 7; // 最多显示的页码数
    const sidePages = 2; // 两端显示的页码数

    // 总是显示第一页
    showPages.push(1);

    if (totalPages <= maxVisiblePages) {
      // 页数较少时，显示所有页码
      for (let i = 2; i <= totalPages; i++) {
        showPages.push(i);
      }
    } else {
      // 页数较多时，使用省略号
      if (currentPage <= sidePages + 3) {
        // 当前页靠近开始
        for (let i = 2; i <= sidePages + 3; i++) {
          showPages.push(i);
        }
        showPages.push("...");
        showPages.push(totalPages);
      } else if (currentPage >= totalPages - (sidePages + 2)) {
        // 当前页靠近结束
        showPages.push("...");
        for (let i = totalPages - (sidePages + 2); i <= totalPages - 1; i++) {
          showPages.push(i);
        }
        showPages.push(totalPages);
      } else {
        // 当前页在中间
        showPages.push("...");
        for (let i = currentPage - sidePages; i <= currentPage + sidePages; i++) {
          showPages.push(i);
        }
        showPages.push("...");
        showPages.push(totalPages);
      }
    }

    // 渲染页码
    showPages.forEach(page => {
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

    // 下一页按钮
    pagination.append(`
      <li class="page-item ${currentPage === totalPages ? "disabled" : ""}">
        <a class="page-link" href="javascript:void(0)" onclick="changePage(${currentPage + 1})">下一页</a>
      </li>
    `);

    footer.append(pagination);
  }
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
  // 获取系统用户和组列表
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
