<template>
  <div class="my-submissions-page">
    <h1><i class="fas fa-file-alt"></i> My Submissions</h1>
    <MySubmissionsList />
  </div>
</template>

<script>
import MySubmissionsList from '@/components/submission/MySubmissionsList.vue';

export default {
  name: 'MySubmissionsPage',
  components: {
    MySubmissionsList
  }
};
</script>

<style scoped>
.my-submissions-page {
  max-width: 1000px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}
</style>