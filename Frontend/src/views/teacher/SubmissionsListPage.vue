<template>
  <div class="submissions-list-page">
    <h1>Submissions</h1>
    <SubmissionsList />
  </div>
</template>

<script>
import SubmissionsList from '@/components/submission/SubmissionsList.vue';

export default {
  name: 'SubmissionsListPage',
  components: {
    SubmissionsList
  }
};
</script>

<style scoped>
.submissions-list-page {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
}
</style>