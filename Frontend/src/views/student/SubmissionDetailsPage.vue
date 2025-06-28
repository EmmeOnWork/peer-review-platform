<template>
  <div class="student-submission-details-page">
    <h1>Details of My Submission</h1>
    <SubmissionDetails />
  </div>
</template>

<script>
import SubmissionDetails from '@/components/submission/SubmissionDetails.vue';

export default {
  name: 'StudentSubmissionDetailsPage',
  components: {
    SubmissionDetails
  }
};
</script>

<style scoped>
.student-submission-details-page {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 20px;
  color: #333;
}
</style>