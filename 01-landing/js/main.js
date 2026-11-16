/**
 * ПАР — интерактив лендинга
 * - мобильное меню
 * - «липкая» шапка
 * - появление блоков при скролле
 * - маска и валидация формы бронирования
 */

(function () {
  'use strict';

  /* ---------- Шапка и мобильное меню ---------- */

  const header = document.getElementById('header');
  const burger = document.getElementById('burger');
  const nav = document.getElementById('nav');

  const onScroll = () => {
    header.classList.toggle('is-scrolled', window.scrollY > 12);
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const closeMenu = () => {
    nav.classList.remove('is-open');
    burger.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
  };

  burger.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('is-open');
    burger.classList.toggle('is-open', isOpen);
    burger.setAttribute('aria-expanded', String(isOpen));
  });

  nav.addEventListener('click', (event) => {
    if (event.target.classList.contains('nav__link')) closeMenu();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  /* ---------- Появление блоков при скролле ---------- */

  const revealItems = document.querySelectorAll('.reveal');

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    revealItems.forEach((item) => observer.observe(item));
  } else {
    revealItems.forEach((item) => item.classList.add('is-visible'));
  }

  /* ---------- Год в подвале ---------- */

  const yearNode = document.getElementById('year');
  if (yearNode) yearNode.textContent = String(new Date().getFullYear());

  /* ---------- Форма бронирования ---------- */

  const form = document.getElementById('bookingForm');
  if (!form) return;

  const success = document.getElementById('formSuccess');
  const phoneInput = form.querySelector('#phone');
  const dateInput = form.querySelector('#date');

  // минимальная дата — сегодня
  const today = new Date();
  const iso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(
    today.getDate()
  ).padStart(2, '0')}`;
  if (dateInput) dateInput.min = iso;

  // маска телефона: +7 (999) 123-45-67
  const formatPhone = (value) => {
    let digits = value.replace(/\D/g, '');

    if (digits.startsWith('8')) digits = '7' + digits.slice(1);
    if (!digits.startsWith('7')) digits = '7' + digits;
    digits = digits.slice(0, 11);

    const parts = [
      '+7',
      digits.slice(1, 4),
      digits.slice(4, 7),
      digits.slice(7, 9),
      digits.slice(9, 11),
    ];

    let result = parts[0];
    if (parts[1]) result += ` (${parts[1]}`;
    if (parts[1].length === 3) result += ')';
    if (parts[2]) result += ` ${parts[2]}`;
    if (parts[3]) result += `-${parts[3]}`;
    if (parts[4]) result += `-${parts[4]}`;
    return result;
  };

  if (phoneInput) {
    phoneInput.addEventListener('input', () => {
      phoneInput.value = formatPhone(phoneInput.value);
    });

    phoneInput.addEventListener('focus', () => {
      if (!phoneInput.value) phoneInput.value = '+7 (';
    });

    phoneInput.addEventListener('blur', () => {
      if (phoneInput.value.replace(/\D/g, '').length <= 1) phoneInput.value = '';
    });
  }

  const setError = (field, message) => {
    const wrapper = field.closest('.form__field') || field.closest('.form__check')?.parentElement;
    const errorNode = form.querySelector(`[data-error-for="${field.id}"]`);

    if (wrapper) wrapper.classList.toggle('is-invalid', Boolean(message));
    if (errorNode) errorNode.textContent = message || '';
  };

  const validators = {
    name(value) {
      if (value.trim().length < 2) return 'Введите имя';
      if (!/^[а-яёa-z\s-]+$/i.test(value.trim())) return 'Только буквы, пробел и дефис';
      return '';
    },
    phone(value) {
      if (value.replace(/\D/g, '').length !== 11) return 'Введите телефон полностью';
      return '';
    },
    date(value) {
      if (!value) return 'Выберите дату';
      if (value < iso) return 'Дата не может быть в прошлом';
      return '';
    },
    agree(checked) {
      if (!checked) return 'Нужно согласие на обработку данных';
      return '';
    },
  };

  const validateField = (field) => {
    const validator = validators[field.name];
    if (!validator) return true;

    const message = validator(field.type === 'checkbox' ? field.checked : field.value);
    setError(field, message);
    return !message;
  };

  form.querySelectorAll('input[required]').forEach((field) => {
    field.addEventListener('blur', () => validateField(field));
    field.addEventListener('input', () => {
      if (field.closest('.form__field')?.classList.contains('is-invalid')) validateField(field);
    });
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    success.hidden = true;

    const fields = Array.from(form.querySelectorAll('input[required]'));
    const isValid = fields.map(validateField).every(Boolean);

    if (!isValid) {
      const firstInvalid = form.querySelector('.is-invalid input') || fields.find((f) => !validateField(f));
      firstInvalid?.focus();
      return;
    }

    // Здесь был бы fetch() на бэкенд/CRM.
    // Для демо: показываем успех и очищаем форму.
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'Отправляем…';

    setTimeout(() => {
      success.hidden = false;
      form.reset();
      fields.forEach((field) => setError(field, ''));
      submitButton.disabled = false;
      submitButton.textContent = 'Забронировать';
      success.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 700);
  });
})();
