document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Clear activity dropdown (keep the default option)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <h5>Participants (${details.participants.length}/${details.max_participants}):</h5>
            <ul>
              ${details.participants.map(participant => `<li><span>${participant}</span><button class="delete-participant" data-activity="${name}" data-email="${participant}" title="Remove participant">×</button></li>`).join('')}
            </ul>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        
        // Refresh activities to show new participant
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Handle delete participant button clicks
  document.addEventListener('click', async (event) => {
    if (event.target.classList.contains('delete-participant')) {
      const button = event.target;
      const activity = button.getAttribute('data-activity');
      const email = button.getAttribute('data-email');

      if (confirm(`Remove ${email} from ${activity}?`)) {
        try {
          const response = await fetch(
            `/activities/${encodeURIComponent(activity)}/signup/${encodeURIComponent(email)}`,
            { method: 'DELETE' }
          );

          if (response.ok) {
            messageDiv.textContent = `Removed ${email} from ${activity}`;
            messageDiv.className = 'success';
            messageDiv.classList.remove('hidden');
            
            // Refresh activities
            await fetchActivities();
            
            setTimeout(() => {
              messageDiv.classList.add('hidden');
            }, 5000);
          } else {
            const result = await response.json();
            messageDiv.textContent = result.detail || 'Failed to remove participant';
            messageDiv.className = 'error';
            messageDiv.classList.remove('hidden');
          }
        } catch (error) {
          messageDiv.textContent = 'Failed to remove participant';
          messageDiv.className = 'error';
          messageDiv.classList.remove('hidden');
          console.error('Error removing participant:', error);
        }
      }
    }
  });

  // Initialize app
  fetchActivities();
});
