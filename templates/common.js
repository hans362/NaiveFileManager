{% raw %}
handleLogout() {
  axios
    .post("/api/user/logout")
    .then((response) => {
      if (response.data.status === "success") {
        window.location.href = "/login";
      } else {
        this.$message.error(response.data.message);
      }
    })
    .catch(() => {
      this.$message.error("退出登录失败");
    });
},
handleMenuClick({ key }) {
  switch (key) {
    case "files":
      window.location.href = "/files";
      break;
    case "logs":
      window.location.href = "/logs";
      break;
    case "users":
      window.location.href = "/users";
      break;
  }
},
validatePassword(password) {
  if (!password) return false;
  
  if (password.length < 12) {
    return '密码长度至少12位';
  }
  
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumbers = /\d/.test(password);
  const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`'"\\]/.test(password);
  
  if (!hasUpperCase || !hasLowerCase || !hasNumbers || !hasSpecialChar) {
    return '密码必须包含大小写字母、数字和特殊字符';
  }
  
  return true;
},
showChangePasswordModal() {
  this.changePasswordForm = {
    old_password: '',
    new_password: '',
    confirm_password: ''
  };
  this.changePasswordVisible = true;
},
handleChangePassword() {
  if (!this.changePasswordForm.old_password || !this.changePasswordForm.new_password || !this.changePasswordForm.confirm_password) {
    this.$message.error('请填写完整信息');
    return;
  }

  if (this.changePasswordForm.new_password !== this.changePasswordForm.confirm_password) {
    this.$message.error('两次输入的新密码不一致');
    return;
  }

  const passwordValidation = this.validatePassword(this.changePasswordForm.new_password);
  if (passwordValidation !== true) {
    this.$message.error(passwordValidation);
    return;
  }

  const params = new URLSearchParams();
  params.append('old_password', this.sm2Encrypt(this.changePasswordForm.old_password));
  params.append('new_password', this.sm2Encrypt(this.changePasswordForm.new_password));

  axios.patch('/api/user/password', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  })
  .then(response => {
    if (response.data.status === 'success') {
      this.$message.success('密码修改成功');
      this.changePasswordVisible = false;
    } else {
      this.$message.error(response.data.message);
    }
  })
  .catch(() => {
    this.$message.error('密码修改失败');
  });
},
sm2Encrypt(data) {
  const publicKey = "{% endraw %}{{ public_key }}{% raw %}";
  return sm2.doEncrypt(data, publicKey);
},
{% endraw %}