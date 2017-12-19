(function (w, d, $) {
    /** @type jQuery */
    var $addSkillsInput,
        $skillList,
        $skillCache = $('<li class="skill"><span class="skill-name"></span></li>');

    /**
     * Appends skills to the $skillList element using the $skillCache element
     * as template.
     * @param skills
     */
    function appendSkills(skills) {
        var skill;

        /** @type jQuery */
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
                .css('display', 'none');
        })
        .on('click', '#add-skills-button', function () {
            $('#pop-up-add-skills', d).css('display', 'block');
        })
        .on('click', '#add-skills-submit-button', function () {
            $.ajax('/skills/add/', {
                method: 'POST',
                data: {
                    skill_ids: $addSkillsInput.val()
                },
                dataType: 'json',
                success: function (skills) {
                    appendSkills(skills);

                    $('#pop-up-add-skills', d)
                        .css('display', 'none');
                },
                error: function () {
                    alert('Error occurred while adding skills, please try again!');
                }
            });
        })
        .on('click', '.skill-endorse-create-button', function () {
            /** @type jQuery */
            var $skill = $(this).parent();

            var userID = $skill.data('user-id'),
                skillID = $skill.data('skill-id');

            $.ajax('/user/' + userID + '/endorse/' + skillID, {
                method: 'POST',
                success: function (endorse) {
                    console.log(endorse);
                },
                error: function () {
                    alert('Error occurred while endorsing, please try again!');
                }
            });
        });
})(window, document, jQuery);
