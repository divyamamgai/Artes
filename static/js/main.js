(function (w, d, $) {
    /** @type JQuery */
    var $addSkillsInput,
        $addSkillsLoading,
        $skillList,
        $skillCache = $('<li class="skill"><span class="skill-name"></span></li>');

    /**
     * Appends skills to the $skillList element using the $skillCache element
     * as template.
     * @param skills
     */
    function appendSkills(skills) {
        var skill;

        /** @type JQuery */
        var $skill;

        for (var skill_index = 0; skill_index < skills.length; skill_index++) {
            skill = skills[skill_index];
            $skill = $skillCache.clone();

            $('.skill-name', $skill)
                .text(skill.name);

            $skillList.append($skill);
        }
    }

    $(function () {
        $addSkillsInput = $('#add-skills-input', d);
        if ($addSkillsInput.length > 0) {
            $addSkillsInput.tokenize2({
                dataSource: function (term, object) {
                    $.ajax('/skills/search/' + encodeURIComponent(term), {
                        dataType: 'json',
                        success: function (skills) {
                            var mapped_skills = skills.map(function (skill) {
                                return {
                                    value: skill.id,
                                    text: skill.name
                                };
                            });

                            object.trigger('tokenize:dropdown:fill',
                                [mapped_skills]);
                        }
                    });
                }
            });
        }
        $addSkillsLoading = $('.add-skills-loading', d);

        $skillList = $('.skill-list', d);
    });
    $(d)
        .on('click', '.message .fa-close', function () {
            // Remove the message shown on clicking close button.
            $(this).parent().remove();
        })
        .on('click', '.pop-up .fa-times-circle', function () {
            // Hide the pop up shown on clicking close button.
            $(this).parent().parent().parent().parent().parent()
                .addClass('hide');
        })
        .on('click', '#add-skills-button', function () {
            $('#pop-up-add-skills', d).removeClass('hide');
        })
        .on('click', '#add-skills-submit-button', function () {
            /** @type JQuery */
            var $addSkillsSubmitButton = $(this);

            $.ajax('/skills/add/', {
                method: 'POST',
                data: {
                    skill_ids: $addSkillsInput.val()
                },
                dataType: 'json',
                beforeSend: function () {
                    $addSkillsSubmitButton.addClass('hide');
                    $addSkillsLoading.removeClass('hide');
                },
                success: function (skills) {
                    appendSkills(skills);

                    $('#pop-up-add-skills', d)
                        .addClass('hide');
                },
                error: function () {
                    alert('Error occurred while adding skills, please try again!');
                },
                complete: function () {
                    $addSkillsSubmitButton.removeClass('hide');
                    $addSkillsLoading.addClass('hide');
                }
            });
        })
        .on('click', '.skill-endorse-create-button', function () {
            /** @type JQuery */
            var $skillEndorseCreateButton = $(this),
                $skill = $skillEndorseCreateButton.parent(),
                $skillEndorseCount = $('.skill-endorse-count', $skill),
                $skillEndorseDeleteButton = $('.skill-endorse-delete-button', $skill),
                $skillOperationLoading = $('.skill-operation-loading', $skill);

            var userID = $skill.data('user-id'),
                skillID = $skill.data('skill-id');

            $.ajax('/user/' + userID + '/endorse/' + skillID, {
                method: 'POST',
                beforeSend: function () {
                    $skillOperationLoading.removeClass('hide');
                    $skillEndorseCreateButton.addClass('hide');
                },
                success: function (endorse) {
                    $skillEndorseCount
                        .text(parseInt($skillEndorseCount.text()) + 1)
                        .removeClass('hide');
                    $skillEndorseDeleteButton.removeClass('hide');
                },
                error: function () {
                    alert('Error occurred while endorsing, please try again!');
                    $skillEndorseCreateButton.removeClass('hide');
                },
                complete: function () {
                    $skillOperationLoading.addClass('hide');
                }
            });
        })
        .on('click', '.skill-endorse-delete-button', function () {
            /** @type JQuery */
            var $skillEndorseDeleteButton = $(this),
                $skill = $skillEndorseDeleteButton.parent(),
                $skillEndorseCount = $('.skill-endorse-count', $skill),
                $skillEndorseCreateButton = $('.skill-endorse-create-button', $skill),
                $skillOperationLoading = $('.skill-operation-loading', $skill);

            var userID = $skill.data('user-id'),
                skillID = $skill.data('skill-id');

            $.ajax('/user/' + userID + '/endorse/' + skillID, {
                method: 'DELETE',
                beforeSend: function () {
                    $skillOperationLoading.removeClass('hide');
                    $skillEndorseDeleteButton.addClass('hide');
                },
                success: function (endorse) {
                    var skillEndorseCount = parseInt($skillEndorseCount.text()) - 1;
                    var $skillEndorserPhotoUser = $('.skill-endorser-photo-user-' + endorse.endorser_id, $skill);
                    $skillEndorseCount
                        .text(skillEndorseCount);
                    if (skillEndorseCount === 0) {
                        $skillEndorseCount.addClass('hide');
                    }
                    $skillEndorseCreateButton.removeClass('hide');
                    $skillEndorseDeleteButton.addClass('hide');
                    if ($skillEndorserPhotoUser.length > 0) {
                        $skillEndorserPhotoUser.remove();
                    }
                },
                error: function () {
                    alert('Error occurred while renouncing your endorsement, please try again!');
                    $skillEndorseDeleteButton.removeClass('hide');
                },
                complete: function () {
                    $skillOperationLoading.addClass('hide');
                }
            });
        })
        .on('click', '.skill-delete-button', function () {
            /** @type JQuery */
            var $skillDeleteButton = $(this),
                $skill = $skillDeleteButton.parent(),
                $skillOperationLoading = $('.skill-operation-loading', $skill);

            var skillID = $skill.data('skill-id');

            $.ajax('/user/skills/' + skillID, {
                method: 'DELETE',
                beforeSend: function () {
                    $skillOperationLoading.removeClass('hide');
                    $skillDeleteButton.addClass('hide');
                },
                success: function (user_skill) {
                    $skill.remove();
                },
                error: function () {
                    alert('Error occurred while deleting skill, please try again!');
                    $skillDeleteButton.removeClass('hide');
                },
                complete: function () {
                    $skillOperationLoading.addClass('hide');
                }
            });
        });
})(window, document, jQuery);
